# boke-N

博客网站（前端 H5 + 后台管理端）版本，主技术栈已切换为：

- 前端：Vue 3 + Vite
- 后端：Python 3 + FastAPI（Cloudflare Workers + D1）

## 功能说明

### 后台管理端（RBAC）

- 管理员登录
- 菜单功能包含：
  - 角色管理
  - 用户管理
  - 资源管理
  - 文章管理
  - 违禁词管理
  - 评论记录管理
- 支持文章发布后前端展示
- 评论内容会校验违禁词

### 前端 H5

- 文章列表 + 文章详情
- 用户注册 / 登录
- 登录后可评论（未登录不可评论）
- 侧边栏展示浏览量 Top10 文章
- 若没有文章，展示默认上海市天气

## 项目结构

```text
backend/   FastAPI API（Cloudflare Worker 入口在 src/main.py）
frontend/  Vue 前端（含管理端与 H5）
db/sqlite/ SQLite 脚本（本地开发）
backend/migrations/ D1 迁移脚本（Cloudflare 部署）
```

## 后端部署（Cloudflare Python Workers + D1）

> Python Workers 目前为 **open beta**，需使用 **pywrangler** CLI 部署。

### 前置要求

- [uv](https://docs.astral.sh/uv/) **>= 0.29.8**
- [Node.js](https://nodejs.org/)
- wrangler **>= 4.64.0**

Windows 用户若 `pywrangler dev` 报 `No module named 'python'`，请先执行 `uv self update` 并清理 `backend/.venv-workers`，详见 [`backend/README.md`](backend/README.md#windows-故障排除)。

### 部署流程

```bash
cd backend

# 1. 安装依赖（项目已初始化，无需再执行 pywrangler init）
uv sync

# 2. 初始化 D1（首次部署）
npx wrangler d1 execute boke-n-db --remote --file=./migrations/0001_schema.sql
npx wrangler d1 execute boke-n-db --remote --file=./migrations/0002_seed.sql

# 3. 本地开发
uv run pywrangler dev          # http://localhost:8787

# 4. 部署到 Cloudflare（需 wrangler login）
uv run pywrangler deploy
```

依赖在 `backend/pyproject.toml` 中管理；`uv run pywrangler dev/deploy` 会自动同步并打包兼容的 Python 包。

> 种子数据已提供可直接使用的 bcrypt 密码：
> - admin / Admin123!
> - demo / Demo123!

更多细节见 [`backend/README.md`](backend/README.md)。

### 本地备用：uvicorn + SQLite

```bash
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

可选环境变量：

```bash
export SQLITE_PATH="backend/data/boke_n.db"
export APP_JWT_SECRET="blog-secret-key-change-me-please-use-env"
```

## 快速启动（前端）

### 1) 启动前端（Vue）

```bash
cd frontend
npm install
npm run dev
```

默认端口：`5173`

### 2) 访问地址

- H5 前端：`http://localhost:5173/`
- 管理端：`http://localhost:5173/?view=admin`

## 默认账号

- 管理员：`admin / Admin123!`
- 普通用户：`demo / Demo123!`

## 已验证

- 后端：`python -m pytest tests/test_api.py` 通过
- 前端：`npm run build` 通过
- API 烟测通过（登录、文章创建、评论、Top10、天气兜底）
- Cloudflare D1 / 本地 SQLite 联调通过（数据实际写入 `users/articles/comments`）

## 后续建议

- 生产环境使用 Cloudflare D1；本地开发可继续使用 SQLite 或 `wrangler d1 --local`。
- 天气接口当前为演示数据，后续可接入真实天气 API。
