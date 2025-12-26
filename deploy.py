#!/usr/bin/env python3
"""
自动化部署脚本
用于完成从代码托管到Vercel部署的全流程
"""

import os
import sys
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deploy.log')
    ]
)
logger = logging.getLogger(__name__)

class DeploymentManager:
    """部署管理器，负责整个部署流程"""

    def __init__(self):
        self.config = {}
        self.github_token = None
        self.vercel_token = None

    def check_dependencies(self):
        """检查必要的依赖"""
        logger.info("检查必要的依赖...")
        required_commands = ['git', 'python3', 'npm']
        for cmd in required_commands:
            if not subprocess.run(['which', cmd], capture_output=True).returncode == 0:
                logger.error(f"缺少必要依赖: {cmd}")
                sys.exit(1)
        logger.info("所有依赖检查通过")

    def get_user_input(self):
        """获取用户输入"""
        print("\n=== 部署配置 ===")
        
        # GitHub配置
        self.github_token = input("请输入GitHub Token (必须有repo权限): ")
        while not self.github_token:
            self.github_token = input("GitHub Token不能为空，请重新输入: ")
        
        # Vercel配置
        use_vercel = input("是否要部署到Vercel? (y/n): ").lower() == 'y'
        if use_vercel:
            self.vercel_token = input("请输入Vercel Token: ")
            while not self.vercel_token:
                self.vercel_token = input("Vercel Token不能为空，请重新输入: ")
        
        # 项目配置
        self.config.update({
            'github': {
                'token': self.github_token,
                'repo_name': input("请输入仓库名称: ") or 'document-chat-assistant',
                'username': input("请输入GitHub用户名: "),
                'private': input("仓库是否私有? (y/n): ").lower() == 'y'
            },
            'vercel': {
                'enabled': use_vercel,
                'token': self.vercel_token if use_vercel else None,
                'project_name': input("请输入Vercel项目名称: ") or 'doc-chat-assistant' if use_vercel else None,
                'domain': input("请输入自定义域名 (可选): ") or None if use_vercel else None
            }
        })

    def generate_config_files(self):
        """生成配置文件"""
        logger.info("生成配置文件...")
        
        # 生成 .env.production
        self._generate_env_production()
        
        # 生成 vercel.json
        if self.config['vercel']['enabled']:
            self._generate_vercel_config()
        
        # 生成 docker-compose.yml
        self._generate_docker_compose()
        
        # 生成 GitHub Actions 工作流
        self._generate_github_workflows()
        
        logger.info("配置文件生成完成")

    def _generate_env_production(self):
        """生成生产环境配置文件"""
        env_content = f"""# AI Services
OPENAI_API_KEY={os.getenv('OPENAI_API_KEY', '')}
DEEPSEEK_API_KEY={os.getenv('DEEPSEEK_API_KEY', '')}
KIMI_API_KEY={os.getenv('KIMI_API_KEY', '')}

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

# Security
SECRET_KEY={os.urandom(24).hex()}
ALLOWED_HOSTS={self.config['vercel']['domain'] if self.config['vercel']['domain'] else '*.vercel.app'}
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
"""
        with open('.env.production', 'w') as f:
            f.write(env_content)

    def _generate_vercel_config(self):
        """生成 Vercel 配置文件"""
        vercel_config = {
            "version": 2,
            "builds": [{
                "src": "app.py",
                "use": "@vercel/python"
            }],
            "routes": [{
                "src": "/(.*)",
                "dest": "app.py"
            }],
            "env": {
                "PYTHON_VERSION": "3.9"
            },
            "functions": {
                "app.py": {
                    "runtime": "python3.9"
                }
            }
        }
        
        if self.config['vercel']['domain']:
            vercel_config["alias"] = [self.config['vercel']['domain']]
        
        with open('vercel.json', 'w') as f:
            json.dump(vercel_config, f, indent=2)

    def _generate_docker_compose(self):
        """生成 Docker Compose 配置"""
        compose_config = {
            "version": "3.8",
            "services": {
                "app": {
                    "build": ".",
                    "ports": ["8501:8501"],
                    "environment": {
                        "OPENAI_API_KEY": os.getenv('OPENAI_API_KEY', ''),
                        "DEEPSEEK_API_KEY": os.getenv('DEEPSEEK_API_KEY', ''),
                        "KIMI_API_KEY": os.getenv('KIMI_API_KEY', ''),
                        "VECTOR_DB_TYPE": "faiss",
                        "VECTOR_STORE_PATH": "./data/vector_store"
                    },
                    "volumes": ["./data:/app/data", "./logs:/app/logs"],
                    "restart": "unless-stopped"
                }
            }
        }
        
        with open('docker-compose.yml', 'w') as f:
            yaml.dump(compose_config, f)

    def _generate_github_workflows(self):
        """生成 GitHub Actions 工作流"""
        workflows_dir = Path('.github/workflows')
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # CI 工作流
        ci_workflow = {
            "name": "CI",
            "on": {
                "push": {"branches": ["main"]},
                "pull_request": {"branches": ["main"]}
            },
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {"python-version": "3.9"}
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -r requirements.txt"
                        },
                        {
                            "name": "Run tests",
                            "run": "pytest"
                        }
                    ]
                }
            }
        }
        
        with open(workflows_dir / 'ci.yml', 'w') as f:
            yaml.dump(ci_workflow, f)

        # Deploy 工作流
        if self.config['vercel']['enabled']:
            deploy_workflow = {
                "name": "Deploy",
                "on": {
                    "push": {"branches": ["main"]}
                },
                "jobs": {
                    "deploy": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {"uses": "actions/checkout@v4"},
                            {
                                "name": "Deploy to Vercel",
                                "uses": "amondnet/vercel-action@v20",
                                "with": {
                                    "vercel-token": self.config['vercel']['token'],
                                    "vercel-org-id": "${{ secrets.ORG_ID }}",
                                    "vercel-project-id": "${{ secrets.PROJECT_ID }}",
                                    "vercel-args": "--prod"
                                }
                            }
                        ]
                    }
                }
            }
            
            with open(workflows_dir / 'deploy.yml', 'w') as f:
                yaml.dump(deploy_workflow, f)

    def setup_github_repo(self):
        """设置 GitHub 仓库"""
        logger.info("设置 GitHub 仓库...")
        
        # 创建 API 请求
        headers = {
            'Authorization': f'token {self.config["github"]["token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        repo_data = {
            'name': self.config['github']['repo_name'],
            'private': self.config['github']['private'],
            'description': 'Document Chat Assistant - AI powered document analysis'
        }
        
        # 创建仓库
        response = requests.post(
            'https://api.github.com/user/repos',
            headers=headers,
            json=repo_data
        )
        
        if response.status_code != 201:
            logger.error(f"创建仓库失败: {response.json()}")
            sys.exit(1)
        
        repo_url = response.json()['clone_url']
        logger.info(f"GitHub 仓库创建成功: {repo_url}")
        
        # 配置远程仓库
        subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
        subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
        
        return repo_url

    def setup_vercel_project(self):
        """设置 Vercel 项目"""
        if not self.config['vercel']['enabled']:
            return
        
        logger.info("设置 Vercel 项目...")
        
        # 安装 Vercel CLI
        subprocess.run(['npm', 'install', '-g', 'vercel'], check=True)
        
        # 登录 Vercel
        subprocess.run(['vercel', 'login', '--token', self.config['vercel']['token']], check=True)
        
        # 链接项目
        subprocess.run(['vercel', 'link'], check=True)
        
        # 设置环境变量
        if os.getenv('OPENAI_API_KEY'):
            subprocess.run(['vercel', 'env', 'add', 'OPENAI_API_KEY'], check=True)
        if os.getenv('DEEPSEEK_API_KEY'):
            subprocess.run(['vercel', 'env', 'add', 'DEEPSEEK_API_KEY'], check=True)
        if os.getenv('KIMI_API_KEY'):
            subprocess.run(['vercel', 'env', 'add', 'KIMI_API_KEY'], check=True)
        
        # 部署项目
        subprocess.run(['vercel', '--prod'], check=True)
        
        logger.info("Vercel 项目设置完成")

    def run_deployment(self):
        """运行完整的部署流程"""
        logger.info("开始部署流程...")
        
        # 检查依赖
        self.check_dependencies()
        
        # 获取用户输入
        self.get_user_input()
        
        # 生成配置文件
        self.generate_config_files()
        
        # 设置 GitHub 仓库
        repo_url = self.setup_github_repo()
        
        # 设置 Vercel 项目
        if self.config['vercel']['enabled']:
            self.setup_vercel_project()
        
        logger.info("部署完成!")
        print(f"\n部署信息:")
        print(f"GitHub 仓库: {repo_url}")
        if self.config['vercel']['enabled']:
            print(f"Vercel 项目: https://{self.config['vercel']['project_name']}.vercel.app")
            if self.config['vercel']['domain']:
                print(f"自定义域名: https://{self.config['vercel']['domain']}")

if __name__ == '__main__':
    try:
        manager = DeploymentManager()
        manager.run_deployment()
    except KeyboardInterrupt:
        logger.info("部署被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"部署失败: {str(e)}")
        sys.exit(1)