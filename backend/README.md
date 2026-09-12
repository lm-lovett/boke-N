# boke-N Backend

Python FastAPI API，生产环境部署在 **Cloudflare Python Workers + D1**（open beta）。

> Python Workers 需要 `python_workers` compatibility flag；本仓库 `wrangler.jsonc` 已配置。

## 前置要求

- [uv](https://docs.astral.sh/uv/) **>= 0.29.8**（Python 包管理器，Windows 需此版本以上才支持 Pyodide）
- [Node.js](https://nodejs.org/)（pywrangler 会代理 wrangler CLI）
- [wrangler](https://developers.cloudflare.com/workers/wrangler/) **>= 4.64.0**（`npm install -g wrangler@latest`）
- **workers-py >= 1.72.0**（已写入 `pyproject.toml` 的 dev 依赖）

Windows 上建议先升级工具链：

```powershell
uv self update
npm install -g wrangler@latest
cd backend
uv sync
```

## 项目结构

```text
backend/
  src/main.py          # Worker 入口（Default = asgi.entrypoint(app)）
  src/app/             # FastAPI 应用与 D1/SQLite 数据层
  wrangler.jsonc       # Worker + D1 绑定配置
  pyproject.toml       # 运行时依赖与 workers-py 开发依赖
  migrations/          # D1 建表与种子数据
  main.py              # 本地 uvicorn 入口（SQLite，仅开发/测试）
```

## 1. 安装依赖

本仓库已完成 `pywrangler init` 等初始化，克隆后只需同步依赖：

```bash
cd backend
uv sync
```

依赖在 `pyproject.toml` 中声明，pywrangler 会在 `dev` / `deploy` 时自动打包兼容的 Python 包：

```toml
[project]
dependencies = ["fastapi", "bcrypt", "pyjwt", "pydantic"]

[dependency-groups]
dev = ["workers-py"]
```

本地跑测试或 uvicorn 时，可临时安装：

```bash
uv add --group dev pytest uvicorn httpx
```

## 2. 初始化 D1 数据库

`wrangler.jsonc` 已绑定：

| 字段 | 值 |
|------|-----|
| binding | `MY_DB` |
| database_name | `boke-n-db` |
| database_id | `0820e294-1a38-44a6-89df-481cb59a9e8b` |

远程（生产）：

```bash
npx wrangler d1 execute boke-n-db --remote --file=./migrations/0001_schema.sql
npx wrangler d1 execute boke-n-db --remote --file=./migrations/0002_seed.sql
```

本地开发：

```bash
npx wrangler d1 execute boke-n-db --local --file=./migrations/0001_schema.sql
npx wrangler d1 execute boke-n-db --local --file=./migrations/0002_seed.sql
```

## 3. 本地开发调试

```bash
uv run pywrangler dev
```

默认地址：`http://localhost:8787`

烟测示例：

```bash
curl http://localhost:8787/api/health
curl -X POST http://localhost:8787/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin123!"}'
```

## 4. 部署到 Cloudflare

需先登录 Cloudflare（`npx wrangler login`），然后：

```bash
uv run pywrangler deploy
```

部署时 Cloudflare 会自动：

- 上传 Python 代码与 `pyproject.toml` 中的依赖
- 注入 Pyodide 运行时并验证代码
- 在部署时执行顶层代码并生成内存快照（减少冷启动）
- 将快照与代码发布到全球网络

## Worker 入口说明

本项目使用 FastAPI + ASGI 适配器（非最简 Hello World 模板）：

```python
from workers import asgi
from app.factory import create_app

app = create_app()
Default = asgi.entrypoint(app)
```

请求进入 Worker 后，通过 `env.MY_DB` 访问 D1：

```python
result = await env.MY_DB.prepare("SELECT * FROM users").all()
```

## 本地备用：uvicorn + SQLite

仅用于不启动 Worker 时的快速调试或自动化测试：

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

## 测试

```bash
uv add --group dev pytest
uv run pytest tests/test_api.py
```

测试使用 SQLite 回退（无 `env.MY_DB` 绑定）。

## 默认账号

- 管理员：`admin / Admin123!`
- 普通用户：`demo / Demo123!`

## Windows 故障排除

若出现类似错误：

```text
ModuleNotFoundError: No module named 'python'
Querying Python at ... pyodide-3.14.2-emscripten-wasm32-musl\python.exe failed
uv venv ...\.venv-workers\pyodide-venv --python cpython-3.14.2-emscripten-wasm32-musl
```

这是 **uv 在 Windows 上创建 Pyodide 虚拟环境** 时的已知问题（旧版 uv / workers-py 更容易触发）。

### 方案 A：升级工具链后重试（推荐）

在 **PowerShell** 中执行：

```powershell
uv self update
npm install -g wrangler@latest
cd D:\my_workspace\boke-N\backend

# 清理 pywrangler 生成的缓存
Remove-Item -Recurse -Force .venv-workers, python_modules, pylock.toml -ErrorAction SilentlyContinue

uv sync
uv run pywrangler sync
uv run pywrangler dev
```

也可直接用最新 pywrangler（不依赖项目内旧版本）：

```powershell
uvx --from workers-py pywrangler sync
uvx --from workers-py pywrangler dev
```

### 方案 B：使用 WSL2（最稳定）

在 WSL2（Ubuntu）中克隆项目并执行 Linux 流程：

```bash
cd backend
uv sync
uv run pywrangler dev
```

Cloudflare 官方对 Python Workers 的本地工具链在 **macOS / Linux / WSL** 上最稳定。

### 方案 C：本地先用 uvicorn，部署用 CI 或 WSL

Windows 上若 `pywrangler dev` 仍失败，可先用 SQLite 模式开发：

```powershell
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

部署时在 WSL 或 GitHub Actions 中执行 `uv run pywrangler deploy`。
