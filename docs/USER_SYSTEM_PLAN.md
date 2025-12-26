# 用户系统架构规划

## 概述

为支持商业化运营，需要实现完整的用户系统，包括认证、订阅、知识库隔离等功能。

---

## 一、用户分层

| 层级 | 目标用户 | 定价建议 | 核心功能 |
|------|----------|----------|----------|
| **免费版** | 体验用户 | ¥0 | 3个文档、10次对话/天 |
| **个人版** | 销售员、主播 | ¥49-99/月 | 20个文档、无限对话、历史记录 |
| **专业版** | 团队、MCN | ¥299-499/月 | 100个文档、团队共享、API接口 |
| **企业版** | 企业培训 | 定制报价 | 无限制、私有部署、定制开发 |

---

## 二、技术架构

### 2.1 认证方案

推荐使用 **NextAuth.js** (Auth.js)，支持多种登录方式：

```
src/
├── app/
│   ├── api/
│   │   └── auth/
│   │       └── [...nextauth]/route.ts  # NextAuth API
│   ├── login/page.tsx                   # 登录页
│   ├── register/page.tsx                # 注册页
│   └── dashboard/page.tsx               # 用户仪表盘
├── lib/
│   └── auth.ts                          # 认证配置
```

支持的登录方式：
- 邮箱密码登录
- 手机验证码登录（阿里云/腾讯云 SMS）
- 微信扫码登录（适合国内用户）
- Google/GitHub OAuth（适合海外用户）

### 2.2 数据库设计

推荐使用 **Prisma** + **PostgreSQL** (Vercel Postgres / Supabase)

```prisma
// prisma/schema.prisma

model User {
  id            String    @id @default(cuid())
  email         String    @unique
  phone         String?   @unique
  name          String?
  avatar        String?
  plan          Plan      @default(FREE)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  documents     Document[]
  conversations Conversation[]
  subscription  Subscription?
}

model Document {
  id        String   @id @default(cuid())
  userId    String
  name      String
  size      Int
  chunks    Int
  content   String   @db.Text
  createdAt DateTime @default(now())

  user      User     @relation(fields: [userId], references: [id])
}

model Conversation {
  id        String    @id @default(cuid())
  userId    String
  title     String?
  createdAt DateTime  @default(now())
  updatedAt DateTime  @updatedAt

  user      User      @relation(fields: [userId], references: [id])
  messages  Message[]
}

model Message {
  id             String       @id @default(cuid())
  conversationId String
  role           String       // 'user' | 'assistant'
  content        String       @db.Text
  sources        String[]
  createdAt      DateTime     @default(now())

  conversation   Conversation @relation(fields: [conversationId], references: [id])
}

model Subscription {
  id            String   @id @default(cuid())
  userId        String   @unique
  plan          Plan
  status        String   // 'active' | 'canceled' | 'expired'
  currentPeriodStart DateTime
  currentPeriodEnd   DateTime
  createdAt     DateTime @default(now())

  user          User     @relation(fields: [userId], references: [id])
}

enum Plan {
  FREE
  PERSONAL
  PROFESSIONAL
  ENTERPRISE
}
```

### 2.3 向量存储方案

生产环境推荐使用云端向量数据库：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **Pinecone** | 易用、Serverless | 国内访问慢 | 海外用户 |
| **Supabase pgvector** | 与Supabase集成 | 需要自己管理 | 全栈Supabase项目 |
| **Weaviate Cloud** | 功能强大 | 学习曲线 | 复杂检索需求 |
| **腾讯云向量数据库** | 国内访问快 | 较新 | 国内用户 |

---

## 三、支付系统

### 3.1 国内支付

推荐使用 **Stripe** 或 **Lemonsqueezy**（海外）+ **微信/支付宝**（国内）

国内支付接入方案：
- **微信支付** - 需要企业资质
- **支付宝** - 需要企业资质
- **Paddle** - 支持个人，但国内体验一般

### 3.2 订阅管理

```typescript
// src/lib/subscription.ts

interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  features: {
    maxDocuments: number;
    maxConversationsPerDay: number;
    historyRetention: number; // days
    teamMembers: number;
    apiAccess: boolean;
  };
}

const PLANS: Record<string, SubscriptionPlan> = {
  FREE: {
    id: 'free',
    name: '免费版',
    price: 0,
    features: {
      maxDocuments: 3,
      maxConversationsPerDay: 10,
      historyRetention: 7,
      teamMembers: 1,
      apiAccess: false,
    },
  },
  PERSONAL: {
    id: 'personal',
    name: '个人版',
    price: 4900, // 分
    features: {
      maxDocuments: 20,
      maxConversationsPerDay: -1, // unlimited
      historyRetention: 30,
      teamMembers: 1,
      apiAccess: false,
    },
  },
  PROFESSIONAL: {
    id: 'professional',
    name: '专业版',
    price: 29900,
    features: {
      maxDocuments: 100,
      maxConversationsPerDay: -1,
      historyRetention: 90,
      teamMembers: 5,
      apiAccess: true,
    },
  },
};
```

---

## 四、实施路线图

### Phase 1: 基础认证（1-2周）
- [ ] 集成 NextAuth.js
- [ ] 邮箱密码注册/登录
- [ ] 用户 Dashboard 页面
- [ ] 知识库与用户关联

### Phase 2: 数据持久化（1-2周）
- [ ] 集成 Prisma + PostgreSQL
- [ ] 文档存储到数据库
- [ ] 对话历史保存
- [ ] 用户配额限制

### Phase 3: 向量存储升级（1周）
- [ ] 集成云端向量数据库
- [ ] 用户级别知识库隔离
- [ ] 文档删除同步

### Phase 4: 支付系统（2周）
- [ ] 集成支付服务
- [ ] 订阅管理页面
- [ ] 配额检查中间件
- [ ] 账单和发票

### Phase 5: 高级功能（持续）
- [ ] 团队协作
- [ ] API 接口
- [ ] 使用分析
- [ ] 移动端适配

---

## 五、部署架构

```
                    ┌─────────────────┐
                    │   Cloudflare    │
                    │   (CDN + WAF)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Vercel      │
                    │   (Next.js)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│   Supabase    │   │   Pinecone    │   │   OpenAI/     │
│  (PostgreSQL) │   │   (Vector)    │   │   DeepSeek    │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## 六、成本估算（月）

| 服务 | 免费额度 | 预计成本 |
|------|----------|----------|
| Vercel Pro | - | $20 |
| Supabase Pro | - | $25 |
| Pinecone Starter | 1个索引 | $0-70 |
| OpenAI API | - | 按量 |
| 域名 | - | ~$12/年 |
| **总计** | - | **$45-115/月** |

---

## 下一步

请确认是否开始实施 Phase 1（基础认证系统），我可以立即开始编写代码。
