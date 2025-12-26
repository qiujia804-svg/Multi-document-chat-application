# Document Chat Assistant 部署指南

## 目录
1. [环境准备](#环境准备)
2. [GitHub配置](#github配置)
3. [Vercel部署](#vercel部署)
4. [Docker部署](#docker部署)
5. [环境变量配置](#环境变量配置)
6. [CI/CD配置](#cicd配置)
7. [监控和日志](#监控和日志)

## 环境准备

### 必需软件
- Python 3.9+
- Git
- Docker (可选)
- Node.js (用于Vercel部署)

### 账号准备
- GitHub账号
- Vercel账号
- AI服务API账号(OpenAI/DeepSeek/Kimi)

## GitHub配置

### 1. 创建仓库
```bash
# 创建新仓库
git clone https://github.com/yourusername/document-chat-assistant.git
cd document-chat-assistant
```

### 2. 配置推送脚本
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

### 3. 分支管理
- main: 生产环境
- develop: 开发环境
- feature/*: 功能分支

## Vercel部署

### 1. 安装Vercel CLI
```bash
npm i -g vercel
```

### 2. 配置vercel.json
```json
{
    "version": 2,
    "builds": [
        {
            "src": "app.py",
            "use": "@vercel/python"
        }
    ],
    "routes": [
        {
            "src": "/(.*)",
            "dest": "app.py"
        }
    ],
    "env": {
        "PYTHON_VERSION": "3.9"
    },
    "functions": {
        "app.py": {
            "runtime": "python3.9"
        }
    }
}
```

### 3. 配置package.json
```json
{
    "name": "document-chat-assistant",
    "version": "1.0.0",
    "scripts": {
        "build": "pip install -r requirements.txt",
        "start": "streamlit run app.py",
        "vercel-build": "pip install -r requirements.txt"
    }
}
```

### 4. 部署步骤
```bash
# 登录Vercel
vercel login

# 部署项目
vercel --prod
```

## Docker部署

### 1. Dockerfile
```dockerfile
# 多阶段构建
FROM python:3.9-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 生产环境
FROM python:3.9-slim

WORKDIR /app

# 复制安装的依赖
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app
USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

### 2. docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - KIMI_API_KEY=${KIMI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  data:
  logs:
```

### 3. .dockerignore
```
.git
.github
__pycache__
*.pyc
*.pyo
*.pyd
.env
.venv
venv/
.gitignore
README.md
Dockerfile
.dockerignore
docker-compose.yml
```

## 环境变量配置

### 1. .env.production
```env
# AI Services
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
KIMI_API_KEY=your_kimi_api_key

# Vector Store
VECTOR_DB_TYPE=faiss
VECTOR_STORE_PATH=/app/data/vector_store

# Document Processing
MAX_FILE_SIZE=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# LLM Configuration
DEFAULT_MODEL=gpt-3.5-turbo
TEMPERATURE=0.7
MAX_TOKENS=4000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# UI Configuration
THEME=light
PAGE_TITLE=Document Chat Assistant
```

### 2. .env.local
```env
# AI Services
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
KIMI_API_KEY=your_kimi_api_key

# Vector Store
VECTOR_DB_TYPE=faiss
VECTOR_STORE_PATH=./vector_store

# Document Processing
MAX_FILE_SIZE=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# LLM Configuration
DEFAULT_MODEL=gpt-3.5-turbo
TEMPERATURE=0.7
MAX_TOKENS=4000

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=app.log

# UI Configuration
THEME=light
PAGE_TITLE=Document Chat Assistant - Development
```

## CI/CD配置

### 1. .github/workflows/ci.yml
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, "3.10"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        
    - name: Test with pytest
      run: |
        pip install pytest
        pytest tests/
        
  docker:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t document-chat-assistant:${{ github.sha }} .
        
    - name: Test Docker image
      run: |
        docker run --rm document-chat-assistant:${{ github.sha }} python -c "import streamlit"
```

### 2. .github/workflows/deploy.yml
```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID }}
        vercel-project-id: ${{ secrets.PROJECT_ID }}
        vercel-args: '--prod'
        
  docker:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
        
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          yourusername/document-chat-assistant:latest
          yourusername/document-chat-assistant:${{ github.sha }}
```

## 监控和日志

### 1. 应用监控
```python
# utils/monitoring.py
import time
import logging
from datetime import datetime

class Monitoring:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def log_request(self, start_time, status_code, error=None):
        duration = time.time() - start_time
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "status_code": status_code
        }
        
        if error:
            log_data["error"] = str(error)
            self.logger.error(log_data)
        else:
            self.logger.info(log_data)
```

### 2. 日志配置
```yaml
# config/logging.yaml
version: 1
disable_existing_loggers: False

formatters:
  default:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  detailed:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"

handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: /app/logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default

loggers:
  "":
    level: INFO
    handlers: [file, console]
```

## 部署后检查清单

### 1. 功能测试
- [ ] 文档上传功能
- [ ] AI服务切换
- [ ] 对话导出
- [ ] 错误处理

### 2. 性能检查
- [ ] 响应时间
- [ ] 内存使用
- [ ] 磁盘空间
- [ ] CPU使用率

### 3. 安全检查
- [ ] API密钥安全
- [ ] 访问控制
- [ ] 数据加密
- [ ] 日志脱敏

### 4. 监控设置
- [ ] 错误告警
- [ ] 性能监控
- [ ] 日志收集
- [ ] 状态检查

## 故障排除

### 常见问题
1. API密钥未配置
2. 向量数据库权限问题
3. 内存不足
4. 网络连接问题

### 解决方案
1. 检查环境变量
2. 确认文件权限
3. 增加内存限制
4. 检查网络配置

## 更新和维护

### 定期任务
1. 更新依赖
2. 备份数据
3. 检查日志
4. 性能优化

### 版本发布流程
1. 功能测试
2. 代码审查
3. 部署预发布
4. 生产部署
5. 监控验证