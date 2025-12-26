# 智能决策顾问

基于知识库的智能问答系统，支持 PDF 和 Word 文档上传，通过 AI 从知识库中精准提取原文内容回答问题。

## 功能特点

- 📄 支持 PDF 和 Word 文档上传
- 🤖 多模型支持：DeepSeek、Kimi 双模型切换
- 📖 严格原文输出：直接引用知识库原文，禁止改写
- 🔄 模型自动降级，确保服务可用性
- 🎨 现代化 UI，支持深色模式

## 输出格式

- 📖 **相关原文** - 直接复制知识库原文，标注来源
- 📌 **关键要点** - 提炼核心信息
- ✅ **建议行动** - 可执行的建议

## 技术栈

- **前端**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **后端**: Next.js API Routes
- **AI**: DeepSeek API, Kimi API
- **部署**: Vercel

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env.local
```

编辑 `.env.local`，填入你的 API 密钥：

```env
# DeepSeek API Key (推荐)
DEEPSEEK_API_KEY=your-deepseek-api-key

# Kimi API Key
KIMI_API_KEY=your-kimi-api-key
```

至少需要配置一个 API 密钥。

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 部署到 Vercel

### 方式一：通过 Vercel CLI

```bash
npm i -g vercel
vercel
```

### 方式二：通过 GitHub 连接

1. 将代码推送到 GitHub
2. 在 Vercel 控制台导入项目
3. 配置环境变量
4. 部署

## API 密钥获取

- **DeepSeek**: https://platform.deepseek.com/
- **Kimi (Moonshot)**: https://platform.moonshot.cn/

## 项目结构

```
src/
├── app/
│   ├── api/
│   │   ├── upload/route.ts   # 文档上传 API
│   │   └── chat/route.ts     # AI 对话 API
│   ├── layout.tsx            # 根布局
│   ├── page.tsx              # 主页
│   └── globals.css           # 全局样式
├── components/
│   ├── FileUpload.tsx        # 文件上传组件
│   ├── ChatInterface.tsx     # 聊天界面组件
│   └── ModelSelector.tsx     # 模型选择器
└── lib/
    ├── document-processor.ts # 文档处理
    └── ai-service.ts         # AI 服务
```

## License

MIT
