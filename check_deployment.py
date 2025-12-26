#!/usr/bin/env python3
"""
部署检查脚本
检查GitHub仓库状态、Vercel部署状态、环境变量配置和API连接
"""

import os
import sys
import json
import requests
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deployment_check.log')
    ]
)
logger = logging.getLogger(__name__)

class DeploymentChecker:
    """部署检查器类"""

    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.vercel_token = os.getenv('VERCEL_TOKEN')
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            sys.exit(1)

    def check_github_status(self) -> Dict[str, Any]:
        """检查GitHub仓库状态"""
        logger.info("检查GitHub仓库状态...")
        
        if not self.github_token:
            return {"status": "error", "message": "GitHub token未配置"}

        try:
            # 获取仓库信息
            repo_owner = self.config.get('github', {}).get('username')
            repo_name = self.config.get('github', {}).get('repo_name')
            
            if not repo_owner or not repo_name:
                return {"status": "error", "message": "GitHub仓库配置不完整"}

            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 检查仓库是否存在
            repo_response = requests.get(
                f'https://api.github.com/repos/{repo_owner}/{repo_name}',
                headers=headers
            )
            
            if repo_response.status_code != 200:
                return {"status": "error", "message": "仓库不存在或无访问权限"}

            repo_info = repo_response.json()
            
            # 检查最新提交
            commits_response = requests.get(
                f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits',
                headers=headers
            )
            
            if commits_response.status_code == 200:
                latest_commit = commits_response.json()[0]['sha']
            else:
                latest_commit = "无法获取"

            # 检查工作流状态
            workflows_response = requests.get(
                f'https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows',
                headers=headers
            )
            
            workflow_status = "未知"
            if workflows_response.status_code == 200:
                workflows = workflows_response.json()['workflows']
                for wf in workflows:
                    if wf['state'] == 'active':
                        workflow_status = "活跃"
                        break

            return {
                "status": "success",
                "repo_name": repo_info['full_name'],
                "private": repo_info['private'],
                "default_branch": repo_info['default_branch'],
                "latest_commit": latest_commit,
                "workflow_status": workflow_status
            }

        except Exception as e:
            return {"status": "error", "message": f"检查GitHub状态失败: {str(e)}"}

    def check_vercel_status(self) -> Dict[str, Any]:
        """检查Vercel部署状态"""
        logger.info("检查Vercel部署状态...")
        
        if not self.vercel_token:
            return {"status": "error", "message": "Vercel token未配置"}

        try:
            headers = {
                'Authorization': f'Bearer {self.vercel_token}',
                'Content-Type': 'application/json'
            }

            # 获取项目信息
            project_id = self.config.get('vercel', {}).get('project_id')
            if not project_id:
                return {"status": "error", "message": "Vercel项目ID未配置"}

            project_response = requests.get(
                f'https://api.vercel.com/v9/projects/{project_id}',
                headers=headers
            )

            if project_response.status_code != 200:
                return {"status": "error", "message": "获取项目信息失败"}

            project_info = project_response.json()

            # 获取最新部署信息
            deployments_response = requests.get(
                f'https://api.vercel.com/v6/projects/{project_id}/deployments',
                headers=headers
            )

            if deployments_response.status_code != 200:
                return {"status": "error", "message": "获取部署信息失败"}

            deployments = deployments_response.json()['deployments']
            if not deployments:
                return {"status": "error", "message": "没有部署记录"}

            latest_deployment = deployments[0]

            return {
                "status": "success",
                "project_name": project_info['name'],
                "latest_deployment": {
                    "url": latest_deployment['url'],
                    "state": latest_deployment['state'],
                    "created": latest_deployment['createdAt']
                },
                "domains": project_info.get('targets', [])
            }

        except Exception as e:
            return {"status": "error", "message": f"检查Vercel状态失败: {str(e)}"}

    def check_environment_variables(self) -> Dict[str, Any]:
        """检查环境变量配置"""
        logger.info("检查环境变量配置...")

        required_vars = {
            'OPENAI_API_KEY': 'OpenAI API密钥',
            'DEEPSEEK_API_KEY': 'DeepSeek API密钥',
            'KIMI_API_KEY': 'Kimi API密钥'
        }

        missing_vars = []
        configured_vars = []

        for var, desc in required_vars.items():
            value = os.getenv(var)
            if value:
                configured_vars.append(var)
            else:
                missing_vars.append(f"{var} ({desc})")

        # 检查其他重要配置
        other_configs = {
            'VECTOR_DB_TYPE': self.config.get('vector_store', {}).get('type'),
            'VECTOR_STORE_PATH': self.config.get('vector_store', {}).get('persist_directory'),
            'CHUNK_SIZE': self.config.get('documents', {}).get('chunk_size'),
            'THEME': self.config.get('ui', {}).get('theme')
        }

        return {
            "status": "success" if not missing_vars else "warning",
            "configured": configured_vars,
            "missing": missing_vars,
            "other_configs": other_configs
        }

    def check_api_connections(self) -> Dict[str, Any]:
        """测试API连接"""
        logger.info("测试API连接...")

        results = {}
        
        # 测试OpenAI
        if os.getenv('OPENAI_API_KEY'):
            try:
                import openai
                client = openai.OpenAI()
                client.models.list()
                results['openai'] = {"status": "success", "message": "连接成功"}
            except Exception as e:
                results['openai'] = {"status": "error", "message": str(e)}
        else:
            results['openai'] = {"status": "warning", "message": "未配置API密钥"}

        # 测试DeepSeek
        if os.getenv('DEEPSEEK_API_KEY'):
            try:
                response = requests.get(
                    'https://api.deepseek.com/v1/models',
                    headers={'Authorization': f'Bearer {os.getenv("DEEPSEEK_API_KEY")}'}
                )
                if response.status_code == 200:
                    results['deepseek'] = {"status": "success", "message": "连接成功"}
                else:
                    results['deepseek'] = {"status": "error", "message": f"HTTP {response.status_code}"}
            except Exception as e:
                results['deepseek'] = {"status": "error", "message": str(e)}
        else:
            results['deepseek'] = {"status": "warning", "message": "未配置API密钥"}

        # 测试Kimi
        if os.getenv('KIMI_API_KEY'):
            try:
                response = requests.get(
                    'https://api.moonshot.cn/v1/models',
                    headers={'Authorization': f'Bearer {os.getenv("KIMI_API_KEY")}'}
                )
                if response.status_code == 200:
                    results['kimi'] = {"status": "success", "message": "连接成功"}
                else:
                    results['kimi'] = {"status": "error", "message": f"HTTP {response.status_code}"}
            except Exception as e:
                results['kimi'] = {"status": "error", "message": str(e)}
        else:
            results['kimi'] = {"status": "warning", "message": "未配置API密钥"}

        return results

    def generate_report(self) -> str:
        """生成检查报告"""
        report = []
        report.append("=== 部署检查报告 ===\n")

        # GitHub状态
        github_status = self.check_github_status()
        report.append("1. GitHub仓库状态")
        if github_status['status'] == 'success':
            report.append(f"   仓库名: {github_status['repo_name']}")
            report.append(f"   私有: {'是' if github_status['private'] else '否'}")
            report.append(f"   默认分支: {github_status['default_branch']}")
            report.append(f"   最新提交: {github_status['latest_commit']}")
            report.append(f"   工作流状态: {github_status['workflow_status']}")
        else:
            report.append(f"   错误: {github_status['message']}")

        # Vercel状态
        vercel_status = self.check_vercel_status()
        report.append("\n2. Vercel部署状态")
        if vercel_status['status'] == 'success':
            report.append(f"   项目名: {vercel_status['project_name']}")
            report.append(f"   最新部署: {vercel_status['latest_deployment']['url']}")
            report.append(f"   部署状态: {vercel_status['latest_deployment']['state']}")
            report.append(f"   部署时间: {vercel_status['latest_deployment']['created']}")
        else:
            report.append(f"   错误: {vercel_status['message']}")

        # 环境变量
        env_status = self.check_environment_variables()
        report.append("\n3. 环境变量配置")
        report.append("   已配置:")
        for var in env_status['configured']:
            report.append(f"   - {var}")
        if env_status['missing']:
            report.append("   缺失:")
            for var in env_status['missing']:
                report.append(f"   - {var}")

        # API连接
        api_status = self.check_api_connections()
        report.append("\n4. API连接状态")
        for service, status in api_status.items():
            report.append(f"   {service.title()}: {status['message']}")

        return "\n".join(report)

    def run_checks(self):
        """运行所有检查"""
        try:
            report = self.generate_report()
            print(report)
            
            # 保存报告到文件
            with open('deployment_report.txt', 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info("检查完成，报告已保存到 deployment_report.txt")

        except Exception as e:
            logger.error(f"检查失败: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    checker = DeploymentChecker()
    checker.run_checks()