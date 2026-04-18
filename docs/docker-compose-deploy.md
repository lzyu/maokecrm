# Docker Compose 部署指南（推荐）

本方案适用于：1 台 Linux 服务器快速上线（前端 `Nginx` + 后端 `FastAPI` + 外部 PostgreSQL）。

## 1. 服务器准备

- Docker 24+
- Docker Compose Plugin（`docker compose version` 可用）
- 服务器放通 80 端口

## 2. 环境变量

```bash
cd backend
cp .env.production.example .env
```

重点修改：

- `DEBUG=false`
- `ENVIRONMENT=production`
- `DATABASE_URL=postgresql://...`（你的外部 PostgreSQL）
- `JWT_SECRET_KEY`（长随机字符串）

## 3. 一键部署

在仓库根目录执行：

```bash
./scripts/deploy-compose.sh
```

启动后访问：

- 前端：`http://<服务器IP>/`
- 后端健康检查：`http://<服务器IP>/api/v1`（业务接口前缀）

> 注：`/api/*` 由前端容器内的 Nginx 反代到后端容器。

## 4. 常用运维命令

```bash
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f frontend
docker compose logs -f backend

# 重启
docker compose restart

# 更新后重建
docker compose build --pull && docker compose up -d
```

## 5. HTTPS（建议）

当前默认是 HTTP。生产建议在服务器外层再加一层 Nginx/Caddy + Let's Encrypt，或使用云负载均衡做 HTTPS 终止。
