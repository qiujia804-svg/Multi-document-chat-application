# 部署脚本使用指南

本文档详细介绍了如何使用自动化部署脚本进行项目部署。

## 目录

1. [脚本概述](#脚本概述)
2. [环境准备](#环境准备)
3. [部署步骤](#部署步骤)
4. [配置生成](#配置生成)
5. [部署检查](#部署检查)
6. [回滚操作](#回滚操作)
7. [常见问题](#常见问题)

## 脚本概述

项目包含以下自动化部署脚本：

1. `deploy.py` - 主要的自动化部署脚本
2. `interactive_deploy.sh` - 交互式部署脚本
3. `generate_config.py` - 配置文件生成器
4. `check_deployment.py` - 部署状态检查器
5. `rollback.sh` - 部署回滚脚本

## 环境准备

### 必需软件

1. Python 3.9+
2. Git
3. Node.js
4. npm

### 环境变量

在开始部署之前，请确保设置以下环境变量：

```bash
export GITHUB_TOKEN=your_github_token
export VERCEL_TOKEN=your_vercel_token
export OPENAI_API_KEY=your_openai_api_key
export DEEPSEEK_API_KEY=your_deepseek_api_key
export KIMI_API_KEY=your_kimi_api_key
```

## 部署步骤

### 使用 deploy.py

1. 直接运行脚本：
```bash
python3 deploy.py
```

2. 脚本将自动：
   - 检查必要的依赖
   - 获取配置信息
   - 生成配置文件
   - 创建 GitHub 仓库
   - 推送代码
   - 部署到 Vercel

### 使用 interactive_deploy.sh

1. 运行交互式脚本：
```bash
./interactive_deploy.sh
```

2. 按照提示选择部署目标：
   - GitHub only
   - GitHub + Vercel

3. 脚本将指导完成整个部署过程。

## 配置生成

### 使用 generate_config.py

1. 运行配置生成器：
```bash
python3 generate_config.py
```

2. 按照提示配置：
   - AI服务
   - 向量存储
   - 文档处理
   - UI设置
   - 日志配置

3. 生成的配置文件：
   - `config.yaml`
   - `.env.production`
   - `.env.local`
   - `vercel.json`
   - `docker-compose.yml`

## 部署检查

### 使用 check_deployment.py

1. 运行检查脚本：
```bash
python3 check_deployment.py
```

2. 检查内容包括：
   - GitHub 仓库状态
   - Vercel 部署状态
   - 环境变量配置
   - API 连接测试

3. 检查结果将保存在 `deployment_report.txt`。

## 回滚操作

### 使用 rollback.sh

1. 运行回滚脚本：
```bash
./rollback.sh
```

2. 回滚过程包括：
   - 选择要回滚的提交
   - 创建备份分支
   - 回滚代码
   - 可选：回滚 Vercel 部署
   - 可选：清理临时文件

## 常见问题

### 1. 权限问题

如果遇到权限错误，请确保：
```bash
chmod +x deploy.py
chmod +x interactive_deploy.sh
chmod +x generate_config.py
chmod +x check_deployment.py
chmod +x rollback.sh
```

### 2. 依赖问题

确保安装了所有必要的依赖：
```bash
# Python 依赖
pip install -r requirements.txt

# Node.js 依赖
npm install -g vercel
```

### 3. 环境变量问题

如果遇到环境变量相关错误：
1. 检查 `.env` 文件是否存在
2. 验证所有必需的环境变量都已设置
3. 确保变量值正确

### 4. 部署失败

如果部署失败：
1. 检查 `deployment_report.txt` 了解详细错误
2. 使用 `check_deployment.py` 进行诊断
3. 考虑使用 `rollback.sh` 回滚到上一个稳定版本

## 示例配置

### 环境变量示例

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Vercel
VERCEL_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# AI Services
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 配置文件示例

```yaml
app:
  name: "Document Chat Assistant"
  version: "2.0.0"

ai_services:
  openai:
    enabled: true
    model: "gpt-3.5-turbo"
    temperature: 0.7
  deepseek:
    enabled: true
    model: "deepseek-chat"
    temperature: 0.7
  kimi:
    enabled: true
    model: "moonshot-v1-8k"
    temperature: 0.7

vector_store:
  type: "faiss"
  persist_directory: "./vector_store"
  similarity_threshold: 0.7

documents:
  max_file_size: 10
  chunk_size: 1000
  chunk_overlap: 200

ui:
  theme: "light"
  page_title: "Document Chat Assistant"
```

## 维护建议

1. 定期运行 `check_deployment.py` 进行健康检查
2. 在进行重大更改前使用 `rollback.sh` 创建备份
3. 定期更新依赖和配置
4. 保持环境变量的安全性
5. 监控部署状态和性能指标