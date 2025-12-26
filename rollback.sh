#!/bin/bash

# 回滚脚本
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

# 获取当前提交历史
get_commit_history() {
    log_info "获取最近10次提交历史..."
    git log --oneline -10
}

# 确认回滚操作
confirm_rollback() {
    echo -e "\n=== 回滚操作确认 ==="
    read -p "确定要回滚到指定提交吗? (y/n): " confirm
    if [[ $confirm != "y" && $confirm != "Y" ]]; then
        log_info "回滚操作已取消"
        exit 0
    fi
}

# 回滚Git仓库
rollback_git() {
    local commit_hash=$1
    log_info "回滚Git仓库到提交: $commit_hash"
    
    # 创建备份分支
    backup_branch="backup-$(date +%Y%m%d-%H%M%S)"
    git checkout -b $backup_branch
    log_success "已创建备份分支: $backup_branch"
    
    # 回滚到指定提交
    git checkout main
    git reset --hard $commit_hash
    
    # 推送更改
    git push --force-with-lease origin main
    log_success "已推送回滚更改到远程仓库"
}

# 回滚Vercel部署
rollback_vercel() {
    log_info "回滚Vercel部署..."
    
    # 安装Vercel CLI
    if ! command -v vercel &> /dev/null; then
        log_info "安装Vercel CLI..."
        npm install -g vercel
    fi
    
    # 登录Vercel
    if [[ -n $VERCEL_TOKEN ]]; then
        echo $VERCEL_TOKEN | vercel login
    else
        vercel login
    fi
    
    # 获取部署历史
    vercel list --limit=10
    
    # 选择要回滚的部署
    read -p "请输入要回滚的部署URL: " deployment_url
    
    if [[ -n $deployment_url ]]; then
        vercel rollback $deployment_url
        log_success "Vercel部署已回滚"
    else
        log_warning "未指定部署URL，跳过Vercel回滚"
    fi
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件和配置..."
    
    # 清理Python缓存
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    
    # 清理日志文件
    if [[ -d logs ]]; then
        rm -f logs/*.log.*
    fi
    
    # 清理临时配置
    rm -f .env.local
    rm -f .env.production
    rm -f deployment_report.txt
    
    log_success "临时文件清理完成"
}

# 检查Git状态
check_git_status() {
    if [[ ! -d .git ]]; then
        log_error "当前目录不是Git仓库"
        exit 1
    fi
    
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "检测到未提交的更改，正在暂存..."
        git stash push -m "Stash before rollback $(date)"
    fi
}

# 主函数
main() {
    echo -e "${BLUE}=== 部署回滚工具 ===${NC}"
    
    # 检查Git状态
    check_git_status
    
    # 显示提交历史
    get_commit_history
    
    # 确认回滚
    confirm_rollback
    
    # 获取要回滚的提交
    read -p "请输入要回滚的提交哈希值: " commit_hash
    
    if [[ -z $commit_hash ]]; then
        log_error "未指定提交哈希值"
        exit 1
    fi
    
    # 执行回滚
    rollback_git $commit_hash
    
    # 询问是否回滚Vercel部署
    read -p "是否需要回滚Vercel部署? (y/n): " rollback_vercel
    if [[ $rollback_vercel == "y" || $rollback_vercel == "Y" ]]; then
        rollback_vercel
    fi
    
    # 询问是否清理临时文件
    read -p "是否清理临时文件和配置? (y/n): " cleanup_files
    if [[ $cleanup_files == "y" || $cleanup_files == "Y" ]]; then
        cleanup
    fi
    
    log_success "回滚操作完成!"
}

# 错误处理
trap 'log_error "回滚过程中发生错误"; exit 1' ERR

# 运行主函数
main "$@"