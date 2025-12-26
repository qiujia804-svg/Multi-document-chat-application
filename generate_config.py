#!/usr/bin/env python3
"""
配置生成器
根据用户输入生成和验证配置文件
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigGenerator:
    """配置生成器类"""

    def __init__(self):
        self.config = {}

    def get_user_input(self) -> Dict[str, Any]:
        """获取用户输入"""
        print("\n=== 配置生成器 ===")
        
        # AI服务配置
        print("\n1. AI服务配置")
        self.config['ai_services'] = {
            'openai': {
                'enabled': self._get_yes_no("是否启用OpenAI服务?"),
                'api_key': input("请输入OpenAI API Key: ") if self._get_yes_no("是否配置OpenAI API Key?") else None,
                'model': input("请输入OpenAI模型 (默认: gpt-3.5-turbo): ") or 'gpt-3.5-turbo',
                'temperature': float(input("请输入temperature (0-1, 默认: 0.7): ") or 0.7),
                'max_tokens': int(input("请输入max_tokens (默认: 4000): ") or 4000)
            },
            'deepseek': {
                'enabled': self._get_yes_no("是否启用DeepSeek服务?"),
                'api_key': input("请输入DeepSeek API Key: ") if self._get_yes_no("是否配置DeepSeek API Key?") else None,
                'model': input("请输入DeepSeek模型 (默认: deepseek-chat): ") or 'deepseek-chat',
                'temperature': float(input("请输入temperature (0-1, 默认: 0.7): ") or 0.7),
                'max_tokens': int(input("请输入max_tokens (默认: 4000): ") or 4000)
            },
            'kimi': {
                'enabled': self._get_yes_no("是否启用Kimi服务?"),
                'api_key': input("请输入Kimi API Key: ") if self._get_yes_no("是否配置Kimi API Key?") else None,
                'model': input("请输入Kimi模型 (默认: moonshot-v1-8k): ") or 'moonshot-v1-8k',
                'temperature': float(input("请输入temperature (0-1, 默认: 0.7): ") or 0.7),
                'max_tokens': int(input("请输入max_tokens (默认: 4000): ") or 4000)
            }
        }

        # 向量存储配置
        print("\n2. 向量存储配置")
        self.config['vector_store'] = {
            'type': input("请输入向量数据库类型 (faiss/chroma, 默认: faiss): ") or 'faiss',
            'persist_directory': input("请输入向量存储路径 (默认: ./vector_store): ") or './vector_store',
            'similarity_threshold': float(input("请输入相似度阈值 (0-1, 默认: 0.7): ") or 0.7)
        }

        # 文档处理配置
        print("\n3. 文档处理配置")
        self.config['documents'] = {
            'max_file_size': int(input("请输入最大文件大小(MB, 默认: 10): ") or 10),
            'chunk_size': int(input("请输入文本块大小 (默认: 1000): ") or 1000),
            'chunk_overlap': int(input("请输入文本块重叠大小 (默认: 200): ") or 200),
            'max_tokens': int(input("请输入最大token数 (默认: 4000): ") or 4000)
        }

        # UI配置
        print("\n4. UI配置")
        self.config['ui'] = {
            'theme': input("请选择主题 (light/dark, 默认: light): ") or 'light',
            'page_title': input("请输入页面标题 (默认: Document Chat Assistant): ") or 'Document Chat Assistant',
            'layout': input("请选择布局 (wide/centered, 默认: wide): ") or 'wide',
            'show_sidebar': self._get_yes_no("是否显示侧边栏? (默认: y): "),
            'chat_height': int(input("请输入聊天界面高度(像素, 默认: 500): ") or 500)
        }

        # 日志配置
        print("\n5. 日志配置")
        self.config['logging'] = {
            'level': input("请输入日志级别 (DEBUG/INFO/WARNING/ERROR, 默认: INFO): ") or 'INFO',
            'format': input("请输入日志格式 (默认: '%(asctime)s - %(name)s - %(levelname)s - %(message)s')") or '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': input("请输入日志文件路径 (默认: app.log): ") or 'app.log',
            'max_size': int(input("请输入日志文件最大大小(MB, 默认: 10): ") or 10),
            'backup_count': int(input("请输入日志文件备份数量 (默认: 5): ") or 5)
        }

        return self.config

    def _get_yes_no(self, prompt: str) -> bool:
        """获取是/否输入"""
        while True:
            response = input(f"{prompt} (y/n): ").lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            print("请输入 y 或 n")

    def generate_files(self):
        """生成配置文件"""
        # 生成 config.yaml
        self._generate_yaml_config()
        
        # 生成 .env.production
        self._generate_env_file('production')
        
        # 生成 .env.local
        self._generate_env_file('local')
        
        # 生成 vercel.json
        self._generate_vercel_config()
        
        # 生成 docker-compose.yml
        self._generate_docker_compose()

    def _generate_yaml_config(self):
        """生成YAML配置文件"""
        config_data = {
            'app': {
                'name': self.config['ui']['page_title'],
                'version': '2.0.0',
                'debug': False
            },
            'ai_services': self.config['ai_services'],
            'vector_store': self.config['vector_store'],
            'documents': self.config['documents'],
            'ui': self.config['ui'],
            'logging': self.config['logging']
        }

        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

    def _generate_env_file(self, env_type: str):
        """生成环境变量文件"""
        filename = f'.env.{env_type}'
        with open(filename, 'w') as f:
            # AI服务API密钥
            for service in ['openai', 'deepseek', 'kimi']:
                if self.config['ai_services'][service]['enabled']:
                    key = f"{service.upper()}_API_KEY"
                    value = self.config['ai_services'][service]['api_key'] or 'your_api_key_here'
                    f.write(f"{key}={value}\n")

            # 向量存储配置
            f.write(f"\n# Vector Store\n")
            f.write(f"VECTOR_DB_TYPE={self.config['vector_store']['type']}\n")
            f.write(f"VECTOR_STORE_PATH={self.config['vector_store']['persist_directory']}\n")

            # 文档处理配置
            f.write(f"\n# Document Processing\n")
            f.write(f"MAX_FILE_SIZE={self.config['documents']['max_file_size']}\n")
            f.write(f"CHUNK_SIZE={self.config['documents']['chunk_size']}\n")
            f.write(f"CHUNK_OVERLAP={self.config['documents']['chunk_overlap']}\n")

            # 日志配置
            f.write(f"\n# Logging\n")
            f.write(f"LOG_LEVEL={self.config['logging']['level']}\n")
            f.write(f"LOG_FILE={self.config['logging']['file']}\n")

            # UI配置
            f.write(f"\n# UI Configuration\n")
            f.write(f"THEME={self.config['ui']['theme']}\n")
            f.write(f"PAGE_TITLE={self.config['ui']['page_title']}\n")

    def _generate_vercel_config(self):
        """生成Vercel配置文件"""
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
            }
        }

        with open('vercel.json', 'w') as f:
            json.dump(vercel_config, f, indent=2)

    def _generate_docker_compose(self):
        """生成Docker Compose配置"""
        compose_config = {
            "version": "3.8",
            "services": {
                "app": {
                    "build": ".",
                    "ports": ["8501:8501"],
                    "environment": {
                        "VECTOR_DB_TYPE": self.config['vector_store']['type'],
                        "VECTOR_STORE_PATH": self.config['vector_store']['persist_directory'],
                        "MAX_FILE_SIZE": str(self.config['documents']['max_file_size']),
                        "CHUNK_SIZE": str(self.config['documents']['chunk_size']),
                        "CHUNK_OVERLAP": str(self.config['documents']['chunk_overlap']),
                        "LOG_LEVEL": self.config['logging']['level'],
                        "THEME": self.config['ui']['theme']
                    },
                    "volumes": [
                        "./data:/app/data",
                        "./logs:/app/logs"
                    ],
                    "restart": "unless-stopped"
                }
            }
        }

        with open('docker-compose.yml', 'w') as f:
            yaml.dump(compose_config, f)

    def validate_config(self) -> bool:
        """验证配置是否有效"""
        try:
            # 验证必需的服务已启用
            enabled_services = [s for s in self.config['ai_services'].keys() 
                             if self.config['ai_services'][s]['enabled']]
            if not enabled_services:
                logger.error("至少需要启用一个AI服务")
                return False

            # 验证向量存储类型
            if self.config['vector_store']['type'] not in ['faiss', 'chroma']:
                logger.error("不支持的向量存储类型")
                return False

            # 验证文本处理参数
            if self.config['documents']['chunk_size'] <= 0:
                logger.error("文本块大小必须大于0")
                return False
            if self.config['documents']['chunk_overlap'] >= self.config['documents']['chunk_size']:
                logger.error("文本块重叠大小必须小于文本块大小")
                return False

            # 验证UI配置
            if self.config['ui']['theme'] not in ['light', 'dark']:
                logger.error("不支持的UI主题")
                return False

            return True

        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return False

    def preview_config(self):
        """显示配置预览"""
        print("\n=== 配置预览 ===")
        print(json.dumps(self.config, indent=2, ensure_ascii=False))

    def run(self):
        """运行配置生成流程"""
        try:
            # 获取用户输入
            self.get_user_input()

            # 验证配置
            if not self.validate_config():
                logger.error("配置验证失败，请检查输入")
                return

            # 显示预览
            self.preview_config()

            # 确认生成
            if self._get_yes_no("\n是否确认生成配置文件?"):
                self.generate_files()
                logger.info("配置文件生成完成")
            else:
                logger.info("配置生成已取消")

        except Exception as e:
            logger.error(f"配置生成失败: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    generator = ConfigGenerator()
    generator.run()