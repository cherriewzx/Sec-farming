#!/bin/bash
# ============================================
# Git 一键上传脚本
# 作者：你自己
# 功能：自动执行 git pull -> add -> commit -> push
# ============================================

# 若未传入提交信息，则默认使用时间戳
if [ -z "$1" ]; then
  COMMIT_MSG="update: $(date '+%Y-%m-%d %H:%M:%S')"
else
  COMMIT_MSG="$1"
fi

echo "📦 开始一键同步到 GitHub..."
echo "🕒 提交信息: $COMMIT_MSG"

# 检查是否是一个 Git 仓库
if [ ! -d .git ]; then
  echo "❌ 当前目录不是 Git 仓库，请先执行 git init 并关联远程仓库。"
  exit 1
fi

# 显示当前状态
git status

# 拉取远程最新版本，防止冲突
echo "⬇️ 拉取远程最新 main 分支..."
git pull origin main --rebase

# 添加所有修改
echo "➕ 添加修改的文件..."
git add .

# 提交更改
echo "💬 提交更改..."
git commit -m "$COMMIT_MSG"

# 推送到远程
echo "🚀 推送到 GitHub..."
git push origin main

echo "✅ 同步完成！"
