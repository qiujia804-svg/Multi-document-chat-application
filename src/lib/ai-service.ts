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
 * Build system prompt - Strict 100% original text mode
 */
function buildSystemPrompt(documents: string[], context: string, hasContext: boolean): string {
  if (!hasContext) {
    return `你是知识库查询助手。回复：知识库未包含此答案。`;
  }

  return `你是知识库查询助手。严格按以下规则回答：

## 知识库原文（唯一信息来源）

${context}

---

## 回答规则（必须100%遵守）

**规则1：完全匹配时（优先）**
若知识库中有与问题直接相关的内容，必须100%原文引用，一字不改：

### 📖 原文引用
> [完整复制原文，不得改动任何字词]

**引用自《文档名》**

**规则2：无完全匹配但有相关内容时**
结合知识库中最相关的段落生成答案，并标注来源：

### 📖 相关内容
> [复制最相关的原文段落]

**引用自《文档名》**

### 💡 综合分析
[基于上述原文内容进行分析，明确说明依据]

**规则3：完全无相关内容时**
直接回复：**知识库未包含此答案**

---

## 绝对禁止
- ❌ 禁止改写、转述、概括原文
- ❌ 禁止添加知识库中不存在的信息
- ❌ 禁止编造内容
- ❌ 禁止使用自己的知识回答

## 输出格式
每次回答必须包含：
1. 📖 原文引用（100%原文复制）
2. 引用来源标注（引用自《文档名》）
3. 如有多段相关内容，全部列出`;
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
        temperature: 0, // Zero temperature for 100% deterministic strict adherence
        max_tokens: 4000,
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
