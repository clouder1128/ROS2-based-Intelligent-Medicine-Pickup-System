# 权限认证模块（Auth）

基于 **JWT**、**RBAC（角色 / 权限）** 与 **审计日志** 的 HTTP API，与主 Flask 应用共用 **`DATABASE_PATH`** 指定的 SQLite 库（见 `auth/db.py` + `common.config.Config`）。

## 目录说明

| 文件 | 作用 |
|------|------|
| `__init__.py` | 对外导出 `auth_bp`、`require_auth`、`require_permissions` 与各权限常量 |
| `blueprint.py` | Flask Blueprint：`/api/auth/*`、`/api/users`、`/api/roles`、`/api/permissions`、`/api/audit/*` |
| `constants.py` | 角色代码、权限码、角色 → 权限映射 |
| `db.py` | SQLite 连接（路径与主配置一致） |
| `schema.py` | 认证相关表结构、`ensure_auth_schema()`、RBAC 种子数据、可选默认管理员 |
| `tokens.py` | JWT 签发 / 解码、访问令牌与刷新令牌 TTL |
| `middleware.py` | `@require_auth`、`@require_permissions(...)` |
| `audit.py` | 审计写入封装 |

蓝图挂载前缀：**`/api`**（例如在应用中注册为 `app.register_blueprint(auth_bp)`）。

## 环境变量

在 **`agent_with_backend/.env`** 或环境中配置：

| 变量 | 说明 | 默认 |
|------|------|------|
| `AUTH_JWT_SECRET` | JWT 签名密钥（生产必填） | 若为空则回退 `FLASK_SECRET_KEY`，再不行则用不安全占位 |
| `AUTH_ACCESS_TTL_SEC` | 访问令牌有效期（秒） | `86400`（24h） |
| `AUTH_REFRESH_TTL_SEC` | 刷新令牌有效期（秒） | `604800`（7d） |
| `AUTH_DEFAULT_ADMIN_PASSWORD` | 仅在库中 **尚无用户** 时创建默认管理员密码 | 空则不创建 |
| `AUTH_DEFAULT_ADMIN_USER` | 默认管理员用户名 | `admin` |
| `AUTH_DEFAULT_ADMIN_EMAIL` | 默认管理员邮箱 | `admin@local` |
| `DATABASE_PATH` | 与业务库同一 SQLite 文件（认证表与库存等业务表共存） | 见 `common/config.py` |

## API 一览（均需 JSON 时注明）

认证与用户：

- `POST /api/auth/register` — 注册（默认角色 `user`）
- `POST /api/auth/login` — 登录，返回 `access_token`、`refresh_token`、`user_info`
- `POST /api/auth/logout` — 注销（可携带刷新令牌作废）
- `POST /api/auth/refresh` — 刷新访问令牌

管理与查询（多数需 **Bearer** + 对应权限）：

- `GET /api/users`、`GET|PUT /api/users/<id>` — 需相应权限（如 `read:users` / `write:users`）
- `GET /api/roles` — 需登录（`@require_auth`）
- `GET /api/permissions` — 需登录；可按 `role_id` 筛选
- `GET /api/audit/logs`、`GET /api/audit/stats` — 需 `read:audit` 等（按路由装饰器）

请求头示例：

```http
Authorization: Bearer <access_token>
```

## 角色与权限（RBAC）

角色代码：`admin`、`pharmacist`、`doctor`、`user`（定义见 `constants.py`）。

权限码示例：`read:drug`、`create:drug`、`update:drug`、`delete:drug`、`read:inventory`、`update:inventory`、`read:users`、`write:users`、`read:audit`。

默认映射概要：

- **admin**：全部权限  
- **pharmacist**：药品 CRUD（含读）、库存读写  
- **doctor**：`read:drug`  
- **user**：`read:drug`  

首次调用会执行 **`ensure_auth_schema()`**：建表并 **`_seed_rbac_if_empty`** 写入角色与权限矩阵。

## 与其它模块集成

- 主入口：`main.py` 中 `register_blueprint(auth_bp)`，并在启动时调用 **`ensure_auth_schema()`**（失败仅告警时可查看控制台）。
- 业务路由可使用：`from auth import require_auth, require_permissions` 及 `PERM_*` 常量保护接口。

## 本地验证示例

启动后端（工作目录 `agent_with_backend`，且已通过配置校验）后：

```bash
# 注册
curl -s -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"secret12","email":"demo@test.local"}'

# 登录（取出 access_token）
curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"secret12"}'

# 携带令牌（请将 TOKEN 设为登录响应中的 access_token）
TOKEN='<access_token>'
curl -s http://localhost:8001/api/roles -H "Authorization: Bearer ${TOKEN}"

# 普通用户无 read:users 时应被拒（例如 403）
curl -s http://localhost:8001/api/users -H "Authorization: Bearer ${TOKEN}"
```

Shell 中务必 **`TOKEN='...'` 单独一行赋值**，再执行带 `$TOKEN` 的 `curl`，避免空令牌。

## 依赖

项目级：`PyJWT`、`Flask`、`werkzeug.security`（密码哈希）。安装见上一级 **`requirements.txt`**。
