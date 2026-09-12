# boke-N

博客网站（前端 H5 + 后台管理端）版本，主技术栈已切换为：

- 前端：Vue 3 + Vite
- 后端：Python 3 + FastAPI

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
backend/   FastAPI API 服务
frontend/  Vue 前端（含管理端与 H5）
db/mysql/  MySQL 建表与初始化脚本
```

## 数据库脚本（MySQL）

已提供完整数据库脚本：

- `db/mysql/001_schema.sql`：建库建表（RBAC + 文章 + 评论 + 违禁词）
- `db/mysql/002_seed.sql`：初始化角色、资源、账号关系、违禁词、演示数据

执行方式示例：

```bash
mysql -uroot -p < db/mysql/001_schema.sql
mysql -uroot -p < db/mysql/002_seed.sql
```

> `002_seed.sql` 已提供可直接使用的 bcrypt 密码（可直接登录）：
> - admin / Admin123!
> - demo / Demo123!

## 快速启动

### 1) 启动后端（FastAPI）

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

默认端口：`8080`

若需指定数据库连接，可设置环境变量：

```bash
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_NAME="boke_n"
export DB_USER="root"
export DB_PASSWORD=""
export APP_JWT_SECRET="blog-secret-key-change-me-please-use-env"
```

### 2) 启动前端（Vue）

```bash
cd frontend
npm install
npm run dev
```

默认端口：`5173`

### 3) 访问地址

- H5 前端：`http://localhost:5173/`
- 管理端：`http://localhost:5173/?view=admin`

## 默认账号

- 管理员：`admin / Admin123!`
- 普通用户：`demo / Demo123!`

## 已验证

- 后端：`python -m pytest tests/test_api.py` 通过
- 前端：`npm run build` 通过
- API 烟测通过（登录、文章创建、评论、Top10、天气兜底）
- MySQL 实库联调通过（数据实际写入 `users/articles/comments`）

## 后续建议

- 当前已切换为 MySQL + PyMySQL 持久化，后续可引入 SQLAlchemy 或迁移到 PostgreSQL。
- 天气接口当前为演示数据，后续可接入真实天气 API。
