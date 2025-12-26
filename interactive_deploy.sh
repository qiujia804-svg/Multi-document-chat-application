#!/bin/bash

# 交互式部署脚本
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要的命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装"
        exit 1
    fi
}

# 检查所有必要的依赖
check_dependencies() {
    log_info "检查必要的依赖..."
    check_command "git"
    check_command "python3"
    check_command "npm"
    log_success "所有依赖检查通过"
}

# 获取用户输入
get_user_input() {
    echo -e "\n=== 部署配置 ==="
    
    # 询问部署目标
    while true; do
        read -p "请选择部署目标 (1: GitHub only / 2: GitHub + Vercel): " target
        case $target in
            1) DEPLOY_TARGET="github"; break;;
            2) DEPLOY_TARGET="vercel"; break;;
            *) log_warning "请输入 1 或 2";;
        esac
    done
    
    # GitHub配置
    read -p "请输入GitHub Token: " GITHUB_TOKEN
    while [ -z "$GITHUB_TOKEN" ]; do
        log_warning "GitHub Token不能为空"
        read -p "请重新输入GitHub Token: " GITHUB_TOKEN
    done
    
    read -p "请输入GitHub用户名: " GITHUB_USERNAME
    read -p "请输入仓库名称 (默认: document-chat-assistant): " REPO_NAME
    REPO_NAME=${REPO_NAME:-document-chat-assistant}
    
    # Vercel配置（如果需要）
    if [ "$DEPLOY_TARGET" = "vercel" ]; then
        read -p "请输入Vercel Token: " VERCEL_TOKEN
        while [ -z "$VERCEL_TOKEN" ]; do
            log_warning "Vercel Token不能为空"
            read -p "请重新输入Vercel Token: " VERCEL_TOKEN
        done
        
        read -p "请输入Vercel项目名称 (默认: doc-chat-assistant): " VERCEL_PROJECT
        VERCEL_PROJECT=${VERCEL_PROJECT:-doc-chat-assistant}
        
        read -p "请输入自定义域名 (可选): " CUSTOM_DOMAIN
    fi
}

# 初始化Git仓库
init_git_repo() {
    log_info "初始化Git仓库..."
    
    if [ ! -d ".git" ]; then
        git init
        git add .
        git commit -m "Initial commit"
    fi
    
    # 创建远程仓库
    if [ "$DEPLOY_TARGET" = "vercel" ]; then
        PRIVATE=false
    else
        while true; do
            read -p "仓库是否私有? (y/n): " is_private
            case $is_private in
                [Yy]*) PRIVATE=true; break;;
                [Nn]*) PRIVATE=false; break;;
                *) log_warning "请输入 y 或 n";;
            esac
        done
    fi
    
    # 创建GitHub仓库
    log_info "创建GitHub仓库..."
    curl -H "Authorization: token $GITHUB_TOKEN" \
         -H "Accept: application/vnd.github.v3+json" \
         https://api.github.com/user/repos \
         -d "{\"name\":\"$REPO_NAME\",\"private\":$PRIVATE}" \
         > /dev/null 2>&1
    
    # 添加远程仓库
    git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
    git push -u origin main
    
    log_success "GitHub仓库创建完成"
}

# 设置Vercel项目
setup_vercel_project() {
    if [ "$DEPLOY_TARGET" != "vercel" ]; then
        return
    fi
    
    log_info "设置Vercel项目..."
    
    # 安装Vercel CLI
    npm install -g vercel
    
    # 登录Vercel
    echo $VERCEL_TOKEN | vercel login
    
    # 创建新项目
    vercel --prod
    
    # 设置环境变量
    if [ ! -z "$OPENAI_API_KEY" ]; then
        echo $OPENAI_API_KEY | vercel env add OPENAI_API_KEY
    fi
    if [ ! -z "$DEEPSEEK_API_KEY" ]; then
        echo $DEEPSEEK_API_KEY | vercel env add DEEPSEEK_API_KEY
    fi
    if [ ! -z "$KIMI_API_KEY" ]; then
        echo $KIMI_API_KEY | vercel env add KIMI_API_KEY
    fi
    
    # 配置自定义域名（如果提供）
    if [ ! -z "$CUSTOM_DOMAIN" ]; then
        vercel domains add $CUSTOM_DOMAIN
    fi
    
    log_success "Vercel项目设置完成"
}

# 显示部署结果
show_deployment_result() {
    echo -e "\n=== 部署结果 ==="
    echo "GitHub仓库: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    
    if [ "$DEPLOY_TARGET" = "vercel" ]; then
        echo "Vercel项目: https://$VERCEL_PROJECT.vercel.app"
        if [ ! -z "$CUSTOM_DOMAIN" ]; then
            echo "自定义域名: https://$CUSTOM_DOMAIN"
        fi
    fi
}

# 主函数
main() {
    log_info "开始交互式部署流程..."
    
    # 检查依赖
    check_dependencies
    
    # 获取用户输入
    get_user_input
    
    # 初始化Git仓库
    init_git_repo
    
    # 设置Vercel项目（如果需要）
    setup_vercel_project
    
    # 显示部署结果
    show_deployment_result
    
    log_success "部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误"; exit 1' ERR

# 运行主函数
main