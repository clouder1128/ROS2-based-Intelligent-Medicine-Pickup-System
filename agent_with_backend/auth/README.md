# 权限认证模块（Auth）

基于 **JWT**、**RBAC（角色 / 权限）** 与 **审计日志** 的 HTTP API，与主 Flask 应用共用 **`DATABASE_PATH`** 指定的 SQLite 库（见 `auth/db.py` + `common.config.Config`）。


## 目录说明

| 文件 | 作用 |
|------|------|
| `__init__.py` | 对外导出 `auth_bp`、`require_auth`、`require_permission`、`require_permissions` 与各 `PERM_*` 常量 |
| `blueprint.py` | Flask Blueprint：`/api/auth/*`、`/api/users`、`/api/roles`、`/api/permissions`、`/api/audit/*` |
| `constants.py` | 角色代码、权限码、`ROLE_PERMISSION_MAP`、`PERMISSION_DESCRIPTIONS` |
| `db.py` | SQLite 连接（路径与主配置一致） |
| `schema.py` | 认证表、`ensure_auth_schema()`、RBAC 种子、可选默认管理员、迁移、**`users` 视图**、**`_sync_permissions_and_role_mappings`** |
| `tokens.py` | JWT 签发 / 解码、Access / Refresh TTL |
| `middleware.py` | `@require_auth`、`@require_permission` / `@require_permissions`、`get_bearer_token`、`get_current_user_from_token` |
| `audit.py` | 审计写入封装 |

蓝图挂载前缀：**`/api`**（在 `main.py` 中 `app.register_blueprint(auth_bp)`）。

## JWT 校验策略（为何不是「每个请求自动验」）

当前 **没有** 全局 `before_request` 对所有 URL 强制 JWT：登录、注册、`verify`、健康检查等需匿名可达；药品、订单等路由通过 **`require_auth` / `require_permission`** 按需保护。

**不要求 Access JWT（Bearer）即可调用的示例**（仍可能有 Body 内 token，如 refresh）：

| 方法 | 路径 |
|------|------|
| GET | `/api/health`、`/api/health/ros2` |
| POST | `/api/auth/register`、`/api/auth/login`、`/api/auth/verify`、`/api/auth/logout`、`/api/auth/refresh` |
| OPTIONS | `/api/order`（CORS 预检） |

其余业务与 `/api/auth/profile`、`/api/users` 等多数需 **`Authorization: Bearer <access_token>`**。

## 环境变量

在 **`agent_with_backend/.env`** 或 shell 环境中配置：

| 变量 | 说明 | 默认 |
|------|------|------|
| `AUTH_JWT_SECRET` | JWT 签名密钥（**生产必填**） | 空则回退 `FLASK_SECRET_KEY`，再不行为开发占位 |
| `AUTH_ACCESS_TTL_SEC` | Access 有效期（秒） | `86400`（24h） |
| `AUTH_REFRESH_TTL_SEC` | Refresh 有效期（秒） | `604800`（7d） |
| `AUTH_DEFAULT_ADMIN_PASSWORD` | 仅在 **`auth_users` 为空** 时创建默认管理员 | 空则不创建 |
| `AUTH_DEFAULT_ADMIN_USER` | 默认管理员用户名 | `admin` |
| `AUTH_DEFAULT_ADMIN_EMAIL` | 默认管理员邮箱 | `admin@local` |
| `AUTH_DEFAULT_ADMIN_DISPLAY_NAME` | 默认管理员展示名 | 未设置则用 `AUTH_DEFAULT_ADMIN_USER` |
| `DATABASE_PATH` | SQLite 路径（与业务表同库） | 见 `common/config.py`（默认 `agent_with_backend/pharmacy.db`） |
| `HOST` / `PORT` | Flask 监听（**由 `main.py` / `Config` 读取，非 auth 独占**） | `0.0.0.0` / `8001` |

## API 一览（均需 JSON 时注明 `Content-Type: application/json`）

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 公开；默认角色 **`patient`**；可选 `display_name`、`email` |
| POST | `/api/auth/login` | 公开；返回 `access_token`、`refresh_token`、`user_info` |
| POST | `/api/auth/verify` | 公开；校验 token（Header `Bearer` 或 Body `token` / `access_token`） |
| GET | `/api/auth/profile` | 需 Bearer Access |
| POST | `/api/auth/logout` | 可选 Body 带 `refresh_token` |
| POST | `/api/auth/refresh` | Body 带 `refresh_token` 换新令牌 |

### 用户与 RBAC

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 需 `read:users` |
| GET / PUT | `/api/users/<id>` | 见 `blueprint.py`（本人或管理员等） |
| GET | `/api/users/<id>/permissions` | Bearer；本人或 `read:users` |
| GET | `/api/roles` | 需 `@require_auth` |
| GET | `/api/permissions` | 需 `@require_auth`；Query `role_id` 可选 |
| GET | `/api/audit/logs`、`/api/audit/stats` | 需 `read:audit` |

请求头示例：

```http
Authorization: Bearer <access_token>
```

## 数据模型与架构对齐

- **物理表**：`auth_users`、`auth_roles`、`auth_permissions`、`auth_role_permissions`、`auth_refresh_tokens`、`auth_audit_logs`。
- **视图 `users`**：`id, username, password_hash, role, display_name, created_at`（`role`：`admin` \| `doctor` \| `pharmacist` \| `patient`）。
- **迁移**：旧角色码 `user` → `patient`；补 `display_name` 等。

## 角色与权限（RBAC）

权限码含：`read:drug`、`create:drug`、`update:drug`、`delete:drug`、`read:inventory`、`update:inventory`、`batch:drug`、`read:approval`、`approve:approval`、`reject:approval`、`read:order`、`read:users`、`write:users`、`read:audit`（完整定义见 `constants.py`）。

默认映射概要（与《团队分工方案2（修订版）》对齐）：

- **admin**：全部上述权限  
- **pharmacist**：药品读/建/改；库存读/改；`read:order`（不含 `delete:drug`、`batch:drug`）  
- **doctor**：`read:drug`、`read:inventory`；审批读/通过/驳回；`read:order`  
- **patient**：仅 `read:drug`  

启动时 **`ensure_auth_schema()`** 会执行 **`_sync_permissions_and_role_mappings`**，使库里角色—权限与 **`ROLE_PERMISSION_MAP`** 一致。

## 与其它模块集成

- `main.py`：`register_blueprint(auth_bp)` + **`ensure_auth_schema()`**。
- 业务蓝图：`from auth import require_auth, require_permission, require_permissions` 及 **`PERM_*`**。

## 本地验证与令牌

工作目录 **`agent_with_backend`**，服务默认 **`http://127.0.0.1:8001`**（若使用 **`PORT=9000`**，下列 URL 中的端口需改掉）。

```bash
# 注册（用户名已存在会返回 AUTH_VAL_003，请换名或改登录）
curl -sS -X POST http://127.0.0.1:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"secret12","email":"demo@test.local"}'

RESP=$(curl -sS -X POST http://127.0.0.1:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"secret12"}')
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -sS http://127.0.0.1:8001/api/auth/profile -H "Authorization: Bearer ${TOKEN}"
```

- **`patient`** 仅能读药品等 `read:drug` 接口；**药品 CRUD 冒烟脚本** `scripts/smoke_drug_api.sh` 需要 **`create:drug` / `update:drug` / `delete:drug`**，请使用 **admin 或 pharmacist** 的 token：

```bash
AUTH_TOKEN='<具备上述权限的 access_token>' ./scripts/smoke_drug_api.sh
# 可选：BASE=http://127.0.0.1:9000 AUTH_TOKEN=... ./scripts/smoke_drug_api.sh
```

- **勿**在公开场合粘贴完整 JWT（等同于临时密码）。

## 常见问题

| 现象 | 处理 |
|------|------|
| `ModuleNotFoundError: No module named 'jwt'` | `pip install PyJWT`（已写入上一级 **`requirements.txt`**） |
| `AUTH_005` 登录失败 | 用户名或密码错误；或使用占位字符串「你的用户名」未改成真实账号 |
| `AUTH_VAL_003` 注册失败 | 用户名已存在，更换 `username` 或使用已有账号登录 |
| `AUTH_403` 调药品写接口 | 当前角色无对应 `PERM_*`，换管理员/药剂师账号 |
| `Port ... is in use` | `PORT=9000 python3 main.py` 或结束占用端口的进程 |

无 ROS2 时可能出现 `rclpy` 相关告警；HTTP 服务仍可在 fallback 下启动（详见 `ros_integration`）。

## 依赖

**`PyJWT`**、`Flask`、`werkzeug.security`（密码哈希）；**`flask-cors`** 等在上一级 **`requirements.txt`**。

```bash
pip install -r requirements.txt
```
