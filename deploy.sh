#!/bin/bash

# 部署脚本
set -e

echo "开始部署 Document Chat Assistant..."

# 检查必需的工具
command -v git >/dev/null 2>&1 || { echo "需要安装 Git"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "需要安装 Docker"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "需要安装 Node.js"; exit 1; }

# 设置环境
ENVIRONMENT=${1:-production}
echo "部署环境: $ENVIRONMENT"

# 更新代码
echo "拉取最新代码..."
git pull origin main

# 运行测试
echo "运行测试..."
python -m pytest tests/

# 构建 Docker 镜像
echo "构建 Docker 镜像..."
docker build -t document-chat-assistant:latest .

# 推送到镜像仓库
if [ "$ENVIRONMENT" = "production" ]; then
    echo "推送到镜像仓库..."
    docker tag document-chat-assistant:latest yourusername/document-chat-assistant:latest
    docker push yourusername/document-chat-assistant:latest
fi

# 部署到 Vercel
echo "部署到 Vercel..."
npm install -g vercel
vercel --prod

# 运行健康检查
echo "运行健康检查..."
sleep 30
curl -f $VERCEL_URL/_stcore/health || exit 1

echo "部署完成!"