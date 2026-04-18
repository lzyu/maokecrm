#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

if [[ ! -f "backend/.env" ]]; then
  echo "ERROR: backend/.env 不存在，请先基于 backend/.env.production.example 创建。"
  exit 1
fi

echo "[1/4] 拉取基础镜像..."
docker compose pull || true

echo "[2/4] 构建镜像..."
docker compose build --pull

echo "[3/4] 启动服务..."
docker compose up -d

echo "[4/4] 当前服务状态:"
docker compose ps

echo "部署完成。请访问: http://<your-server-ip>/"
