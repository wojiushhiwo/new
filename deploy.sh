#!/bin/bash
# =============================================
# 跑刀避雷指南 - 部署脚本
# 用法:
#   ./deploy.sh           查看当前状态
#   ./deploy.sh staging   把 staging 分支的改动上线
#   ./deploy.sh rollback  回滚到上一个版本
# =============================================

set -e
APP_DIR="/var/www/paodao-review-server"
SERVICE="bileizhinan"

cd "$APP_DIR"

case "${1:-status}" in
  status)
    echo "=== 当前分支: $(git branch --show-current) ==="
    echo "=== 最新提交 ==="
    git log --oneline -3
    echo ""
    echo "=== 未提交改动 ==="
    git status -s
    echo ""
    echo "=== staging 相比 master 的改动 ==="
    git log master..staging --oneline 2>/dev/null || echo "(无)"
    echo ""
    echo "=== 服务状态 ==="
    systemctl is-active "$SERVICE" --quiet && echo "● 运行中" || echo "○ 已停止"
    ;;

  staging)
    echo "▶ 正在部署 staging 分支..."
    
    # 暂存当前 master 的未提交改动（如果有）
    if [ -n "$(git status -s)" ]; then
      git stash push -m "auto-stash before deploy $(date +%Y%m%d%H%M)"
    fi
    
    # 合并 staging 到 master
    git checkout master
    git merge staging --no-edit
    
    # 重启服务
    systemctl restart "$SERVICE"
    echo "✅ 部署完成，服务已重启"
    git log --oneline -1
    ;;

  rollback)
    echo "◀ 正在回滚到上一个版本..."
    git checkout master
    git log --oneline -5
    echo ""
    read -p "回滚到哪个提交？(输入 commit hash): " HASH
    if [ -n "$HASH" ]; then
      git revert --no-edit "$HASH" || git reset --hard "$HASH"
      systemctl restart "$SERVICE"
      echo "✅ 已回滚，服务已重启"
    else
      echo "已取消"
    fi
    ;;

  *)
    echo "用法: ./deploy.sh [status|staging|rollback]"
    ;;
esac
