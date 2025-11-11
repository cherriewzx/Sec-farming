#!/bin/bash
# 用法： ./push.sh <文件名>
# 例如： ./push.sh readme.md

file=$1

if [ -z "$file" ]; then
  echo "❗请输入要提交的文件名，例如：./push.sh readme.md"
  exit 1
fi

git add "$file"
git commit -m "update $file"
git push origin main