import OpenAI from 'openai';
import { searchVectorStore, getStoredDocuments, getTotalChunksCount } from './document-processor';

type ModelType = 'deepseek' | 'kimi';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface ChatResult {
  response: string;
  sources: string[];
  model: string;
}

const modelConfigs: Record<ModelType, {
  apiKey: string | undefined;
  baseURL: string;
  model: string;
  displayName: string;
}> = {
  deepseek: {
    apiKey: process.env.DEEPSEEK_API_KEY,
    baseURL: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    displayName: 'DeepSeek',
  },
  kimi: {
    apiKey: process.env.KIMI_API_KEY,
    baseURL: 'https://api.moonshot.cn/v1',
    model: 'moonshot-v1-8k',
    displayName: 'Kimi',
  },
};

function getClient(modelType: ModelType): OpenAI {
  const config = modelConfigs[modelType];
  if (!config.apiKey) {
    throw new Error(`API key for ${modelType} is not configured`);
  }
  return new OpenAI({
    apiKey: config.apiKey,
    baseURL: config.baseURL,
  });
}

/**
 * Build system prompt - Strict original text mode
 */
function buildSystemPrompt(documents: string[], context: string, hasContext: boolean): string {
  if (!hasContext) {
    return `你是知识库查询助手。当前未找到相关内容，请用户调整问题或上传相关文档。`;
  }

  return `你是知识库查询助手。你的唯一任务是从知识库中提取并展示原文内容。

## 知识库原文

${context}

---

## 输出要求（严格遵守）

根据用户问题，从上方知识库原文中找出相关内容，按以下格式输出：

### 📖 相关原文

直接复制粘贴知识库中与问题相关的段落，保持原文不变。每段标注来源。

格式：
**来源：《文档名》**
> 直接粘贴原文，一字不改

（如有多段相关内容，全部列出）

### 📌 关键要点

用简短的要点形式，提炼原文中的核心信息（不是改写，是提炼关键词）。

### ✅ 建议行动

基于原文内容，给出1-3条可执行的建议。

---

**禁止事项：**
- 禁止改写原文
- 禁止编造不存在的内容
- 禁止添加原文中没有的信息
- 所有内容必须来自上方知识库原文`;
}

export async function chat(
  message: string,
  modelType: ModelType = 'deepseek',
  history: ChatMessage[] = []
): Promise<ChatResult> {
  if (!['deepseek', 'kimi'].includes(modelType)) {
    modelType = 'deepseek';
  }

  const documents = getStoredDocuments();
  const totalChunks = getTotalChunksCount();

  console.log(`[Chat] Query: "${message}"`);
  console.log(`[Chat] Documents: ${documents.join(', ') || 'none'}, Total chunks: ${totalChunks}`);

  const relevantChunks = await searchVectorStore(message, 10);
  console.log(`[Chat] Retrieved ${relevantChunks.length} chunks`);

  let context = '';
  const sources: string[] = [];

  if (relevantChunks.length > 0) {
    context = relevantChunks
      .map((chunk, index) => {
        const docName = chunk.metadata.fileName;
        if (!sources.includes(docName)) {
          sources.push(docName);
        }
        return `【第${index + 1}段】来源：《${docName}》
"${chunk.text}"`;
      })
      .join('\n\n---\n\n');
  }

  const hasContext = context.length > 0;
  const systemPrompt = buildSystemPrompt(documents, context, hasContext);

  const messages: ChatMessage[] = [
    { role: 'system', content: systemPrompt },
    ...history.slice(-4),
    { role: 'user', content: message },
  ];

  const modelOrder: ModelType[] = modelType === 'kimi' ? ['kimi', 'deepseek'] : ['deepseek', 'kimi'];
  let lastError: Error | null = null;

  for (const model of modelOrder) {
    try {
      const config = modelConfigs[model];
      if (!config.apiKey) continue;

      console.log(`[Chat] Using: ${config.displayName}`);
      const client = getClient(model);

      const completion = await client.chat.completions.create({
        model: config.model,
        messages: messages.map(m => ({ role: m.role, content: m.content })),
        temperature: 0.2, // Very low for strict adherence
        max_tokens: 3000,
      });

      const response = completion.choices[0]?.message?.content || '无法生成回复';
      console.log(`[Chat] Response from ${config.displayName}`);

      return { response, sources, model: config.displayName };
    } catch (error) {
      lastError = error as Error;
      console.error(`[Chat] Error from ${model}:`, error);
    }
  }

  throw lastError || new Error('AI服务失败，请检查API密钥');
}

export function getAvailableModels(): { id: ModelType; name: string; available: boolean }[] {
  return Object.entries(modelConfigs).map(([id, config]) => ({
    id: id as ModelType,
    name: config.displayName,
    available: !!config.apiKey,
  }));
}
