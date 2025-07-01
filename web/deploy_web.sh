#!/usr/bin/env bash
# deploy.sh — 自动化前端构建并发布到 nginx
# 2025-06-26 Asia/Tokyo

set -uo pipefail

run() {
  echo -e "\n▶ $*"
  if ! "$@"; then
    echo "✖ 失败：$*" >&2
    exit 1
  fi
}

SRC_DIR="/home/ai/rag/ragflow_web_project"
DIST_DIR="$SRC_DIR/dist"
TARGET_DIR="/home/ai/rag/ragflow_web/rag"

# 1. 进入项目目录
run cd "$SRC_DIR"

# 2. 删除 dist
if [ -e "$DIST_DIR" ]; then
  run rm -rf "$DIST_DIR"
else
  echo "⚠️ 跳过：$DIST_DIR 不存在"
fi

# 3. 验证 dist 已被删除
if [ -e "$DIST_DIR" ]; then
  echo "✖ $DIST_DIR 删除失败" >&2
  exit 1
else
  echo "✔ $DIST_DIR 已删除"
fi

# —— 优化点：增加 Node 内存、更新 browserslist —— 

# 3.1 更新 caniuse-lite 数据库，消除警告
echo -e "\n▶ 更新 caniuse-lite 数据库"
npx update-browserslist-db@latest --update-db || true

# 3.2 给 Node 分配更大内存（比如 4GB）
export NODE_OPTIONS="--max_old_space_size=5120"
echo "✔ NODE_OPTIONS = $NODE_OPTIONS"

# 4. 执行 npm 构建
run npm run build

# 5. 清空旧的 /rag 内容（保留 rag 目录本身）
if [ -d "$TARGET_DIR" ]; then
  run find "$TARGET_DIR" -mindepth 1 -delete
else
  echo "✖ 目标目录不存在：$TARGET_DIR" >&2
  exit 1
fi

# 6. 拷贝 dist 下所有内容（包括隐藏文件）到 TARGET_DIR
run cp -r "$DIST_DIR/." "$TARGET_DIR/"

# 7. 让 nginx 重新加载配置／静态文件
run sudo systemctl reload nginx

echo -e "\n✅ 部署完成！"
