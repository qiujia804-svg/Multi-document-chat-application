# Document Chat Assistant 完整部署指南

## 目录
1. [环境准备](#环境准备)
2. [GitHub设置](#github设置)
3. [Vercel部署](#vercel部署)
4. [Docker部署](#docker部署)
5. [环境变量配置](#环境变量配置)
6. [域名和SSL配置](#域名和ssl配置)
7. [监控和日志](#监控和日志)
8. [常见问题解决](#常见问题解决)

## 环境准备

### 必需软件
- Python 3.9+
- Git
- Docker
- Node.js (用于Vercel CLI)

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/yourusername/document-chat-assistant.git
cd document-chat-assistant

# 创建Python虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## GitHub设置

### 1. 创建仓库
1. 登录GitHub，创建新仓库
2. 克隆仓库到本地
3. 添加远程仓库：
```bash
git remote add origin https://github.com/yourusername/document-chat-assistant.git
```

### 2. 配置GitHub Secrets
在仓库设置中添加以下Secrets：
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `KIMI_API_KEY`
- `VERCEL_TOKEN`
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `ORG_ID` (Vercel组织ID)
- `PROJECT_ID` (Vercel项目ID)

### 3. 配置推送脚本
Windows (push.bat):
```batch
@echo off
git add .
git commit -m "Update: %date% %time%"
git push origin main
```

Linux/Mac (push.sh):
```bash
#!/bin/bash
git add .
git commit -m "Update: $(date)"
git push origin main
```

## Vercel部署

### 1. 安装Vercel CLI
```bash
npm i -g vercel
```

### 2. 连接项目
```bash
# 登录Vercel
vercel login

# 链接项目
vercel link

# 设置环境变量
vercel env add OPENAI_API_KEY
vercel env add DEEPSEEK_API_KEY
vercel env add KIMI_API_KEY
```

### 3. 配置vercel.json
检查vercel.json配置是否正确：
- 确保Python版本为3.9+
- 设置正确的构建和启动命令
- 配置安全头部

### 4. 部署
```bash
# 开发环境部署
vercel

# 生产环境部署
vercel --prod
```

## Docker部署

### 1. 本地构建
```bash
# 构建镜像
docker build -t document-chat-assistant .

# 运行容器
docker run -p 8501:8501 document-chat-assistant
```

### 2. Docker Compose部署
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 生产环境配置
1. 使用docker-compose.prod.yml
2. 配置环境变量文件
3. 设置资源限制
4. 配置健康检查

## 环境变量配置

### 1. 复制环境变量模板
```bash
cp .env.example .env.local  # 开发环境
cp .env.example .env.production  # 生产环境
```

### 2. 配置API密钥
在相应环境中设置：
- OpenAI API Key
- DeepSeek API Key
- Kimi API Key

### 3. 配置服务参数
- 向量数据库类型
- 文档处理参数
- LLM参数

## 域名和SSL配置

### 1. 域名设置
Vercel:
1. 在Vercel控制台添加自定义域名
2. 配置DNS记录
3. 等待SSL证书生成

Docker:
1. 使用Nginx反向代理
2. 配置Let's Encrypt证书
3. 设置自动续期

### 2. SSL配置
Nginx示例配置:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 监控和日志

### 1. 应用监控
1. 配置Prometheus指标
2. 设置Grafana仪表盘
3. 配置告警规则

### 2. 日志管理
1. 使用ELK Stack
2. 配置日志收集
3. 设置日志轮转

### 3. 错误追踪
1. 集成Sentry
2. 配置错误报告
3. 设置错误告警

## 常见问题解决

### 1. 部署失败
- 检查环境变量
- 验证依赖版本
- 查看详细错误日志

### 2. 性能问题
- 优化向量索引
- 调整并发限制
- 使用缓存

### 3. 安全问题
- 定期更新依赖
- 审查API密钥
- 配置防火墙

### 4. 数据备份
- 定期备份向量数据库
- 导出对话历史
- 备份配置文件

## 维护指南

### 1. 定期任务
- 更新依赖
- 清理日志
- 备份数据

### 2. 版本发布
1. 创建功能分支
2. 测试和审查
3. 合并到主分支
4. 触发部署
5. 验证功能

### 3. 应急响应
1. 监控告警
2. 快速定位问题
3. 回滚方案
4. 修复和更新