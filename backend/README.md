# boke-N Backend

Python FastAPI API，支持两种运行方式：

1. **Cloudflare Python Workers + D1**（生产推荐）
2. **本地 uvicorn + SQLite**（本地开发与自动化测试）

## Cloudflare Workers + D1

### 配置

`wrangler.jsonc` 已绑定 D1 数据库：

- binding: `MY_DB`
- database_name: `boke-n-db`
- database_id: `0820e294-1a38-44a6-89df-481cb59a9e8b`

### 初始化 D1 数据库

```bash
cd backend
npx wrangler d1 execute boke-n-db --remote --file=./migrations/0001_schema.sql
npx wrangler d1 execute boke-n-db --remote --file=./migrations/0002_seed.sql
```

本地开发数据库：

```bash
npx wrangler d1 execute boke-n-db --local --file=./migrations/0001_schema.sql
npx wrangler d1 execute boke-n-db --local --file=./migrations/0002_seed.sql
```

### 本地运行 Worker

```bash
cd backend
uv sync
uv run pywrangler dev
```

默认地址：`http://localhost:8787`

### 部署

```bash
cd backend
uv run pywrangler deploy
```

## 本地 uvicorn（SQLite）

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

首次启动会自动初始化 `data/boke_n.db`。

## 测试

```bash
cd backend
python -m pytest tests/test_api.py
```
