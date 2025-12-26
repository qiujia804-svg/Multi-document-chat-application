#!/bin/bash

# 环境设置脚本
set -e

echo "设置 Document Chat Assistant 开发环境..."

# 检查必需的工具
command -v python3 >/dev/null 2>&1 || { echo "需要安装 Python 3.9+"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "需要安装 Git"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "需要安装 Docker"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "需要安装 Node.js"; exit 1; }

# 创建虚拟环境
echo "创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
echo "安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 安装 Node.js 依赖
echo "安装 Node.js 依赖..."
npm install -g vercel

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p data logs vector_store

# 复制环境变量文件
echo "设置环境变量..."
if [ ! -f .env.local ]; then
    cp .env.example .env.local
    echo "请编辑 .env.local 文件并添加您的 API 密钥"
fi

# 初始化 Git
if [ ! -d .git ]; then
    echo "初始化 Git 仓库..."
    git init
    git add .
    git commit -m "Initial commit"
    git remote add origin https://github.com/yourusername/document-chat-assistant.git
fi

# 运行测试
echo "运行测试..."
python -m pytest tests/ -v

echo "环境设置完成!"
echo "请记得:"
echo "1. 编辑 .env.local 文件并添加您的 API 密钥"
echo "2. 运行 'streamlit run app.py' 启动开发服务器"
echo "3. 访问 http://localhost:8501 查看应用"