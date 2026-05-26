# 项目API接口分层改造方案

## 当前项目 API 现状

### 现有外部API端点（`backend/controllers/`）

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/drugs` | GET | 药品列表（支持 name 筛选） |
| `/api/drugs/<id>` | GET | 单个药品详情 |
| `/api/order` | POST | 创建订单 |
| `/api/approve` | POST | 审批操作 |
| `/api/health` | GET | 健康检查 |
| `/api/orders` | GET | 订单列表 |

### 核心模块间依赖

```
P1/ (智能筛选)  ──HTTP调用──>  backend/ (药品API)
backend/  ──直接SQL──>  SQLite
```

---

## 当前状况：两层结构

目前项目只有两层：

```
Controller ──→ 直接操作数据库
```

### 示例：当前 `controllers/drug_controller.py`

```python
@drug_bp.route("/drugs", methods=["GET"])
def list_drugs():
    name_filter = request.args.get("name")
    conn = get_db_connection()
    cur = conn.execute(
        "SELECT drug_id, name, quantity, ... FROM inventory WHERE name LIKE ?",
        (f"%{name_filter}%",),
    )
    drugs = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"success": True, "drugs": drugs, "count": len(drugs)})
```

### 问题

- Controller 里混着 SQL 查询，看不懂业务逻辑
- 智能筛选系统（P1）无法复用这个查询，只能自己再调一次HTTP
- 要测试这个函数，必须要有真实数据库

---

## 目标：四层架构

```
┌─────────────────────────────────────────────────┐
│                  前端 (React)                     │
│       只看 OpenAPI spec，不关心后端实现            │
├─────────────────────────────────────────────────┤
│  API 网关层 (controllers/)                        │
│  ─── 接收HTTP请求 → 解析参数 → 调Service层        │
│  ─── 序列化响应 → 返回HTTP响应                     │
│  契约来源: OpenAPI 3.0 规范文件                    │
├─────────────────────────────────────────────────┤
│  业务逻辑层 (services/)  ← 新增目录                │
│  ─── DrugService / OrderService / AuthService     │
│  ─── 只依赖 Protocol 接口，不依赖具体实现           │
│  契约来源: Python Protocol 抽象                    │
├─────────────────────────────────────────────────┤
│  数据访问层 (repositories/)  ← 新增目录            │
│  ─── DrugRepository / OrderRepository              │
│  ─── 实现 Protocol，操作数据库                     │
│  契约来源: Python Protocol 抽象                    │
├─────────────────────────────────────────────────┤
│  基础设施层 (utils/ + 外部系统)                    │
│  ─── SQLite / ROS2 / LLM API                     │
└─────────────────────────────────────────────────┘
```

---

## 四层详解——用现有代码演示

### 层1：API 网关层 (Controller) — 只管"接请求、返响应"

```python
# controllers/drug_controller.py  —— 改造后
from ..services.drug_service import DrugServiceProtocol  # 只依赖接口

@drug_bp.route("/drugs", methods=["GET"])
def list_drugs():
    name_filter = request.args.get("name")

    # 调 Service 层，不碰数据库
    drugs = drug_service.search_by_name(name_filter)

    return jsonify({"success": True, "drugs": drugs, "count": len(drugs)})
```

**职责**：参数解析 → 调 Service → JSON序列化 → 返回  
**不做什么**：不写 SQL、不做业务校验、不处理缓存

---

### 层2：业务逻辑层 (Service) — 负责"业务流程和规则"

```python
# services/drug_service.py  —— 新增
from typing import Protocol, List, Dict, Any
from ..repositories.drug_repository import DrugRepositoryProtocol

# Step A：定义接口契约（Protocol）
class DrugServiceProtocol(Protocol):
    def search_by_name(self, name: str) -> List[Dict[str, Any]]: ...
    def get_low_stock_drugs(self, threshold: int) -> List[Dict[str, Any]]: ...
    def search_by_symptom(self, symptom: str) -> List[Dict[str, Any]]: ...

# Step B：实现业务逻辑
class DrugService:
    def __init__(self, repo: DrugRepositoryProtocol):  # 依赖 Repository 接口
        self.repo = repo

    def search_by_name(self, name: str):
        # 可以在这里加业务规则，比如：
        if len(name) > 100:
            return []  # 拒绝过长查询

        drugs = self.repo.find_by_name(name)
        # 还可以做后处理：排序、过滤过期药品等
        return drugs

    def get_low_stock_drugs(self, threshold: int):
        all_drugs = self.repo.find_all()
        return [d for d in all_drugs if d["quantity"] < threshold]

    def search_by_symptom(self, symptom: str):
        # 这里可以调 LLM 做症状匹配，再调 Repository 查数据库
        # 但 Repository 不知道 LLM，Service 负责编排
        pass
```

**职责**：实现业务规则（低库存判定、过期处理、症状匹配）  
**不做什么**：不写 SQL、不处理 HTTP 请求

---

### 层3：数据访问层 (Repository) — 只管"怎么查数据"

```python
# repositories/drug_repository.py  —— 新增
from typing import Protocol, List, Dict, Any
from ..utils.database import get_db_connection

# 接口定义
class DrugRepositoryProtocol(Protocol):
    def find_all(self) -> List[Dict[str, Any]]: ...
    def find_by_name(self, name: str) -> List[Dict[str, Any]]: ...
    def find_by_id(self, drug_id: int) -> Dict[str, Any]: ...

# SQLite 实现
class SqliteDrugRepository:
    def find_by_name(self, name: str):
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT * FROM inventory WHERE name LIKE ?",
            (f"%{name}%",),
        )
        result = [dict(row) for row in cur.fetchall()]
        conn.close()
        return result

    def find_all(self):
        conn = get_db_connection()
        cur = conn.execute("SELECT * FROM inventory")
        result = [dict(row) for row in cur.fetchall()]
        conn.close()
        return result
```

**职责**：只做数据的读取和写入，不包含业务逻辑  
**不做什么**：不做 if-else 业务判断、不调 LLM

---

### 层4：基础设施层 (Infrastructure) — 现有 `utils/` 和外部系统

这部分基本不变，保持现有的：
- `utils/database.py` — SQLite 连接
- `utils/ros2_bridge.py` — ROS2 通信
- P1 中的 LLM 客户端

---

## 改造后团队协作方式

### 场景1：智能筛选团队需要药品数据

**当前方式** — P1直接调HTTP：

```python
# P1/services/pharmacy_client.py —— 当前
def query_drugs_by_symptom(symptom):
    client = _get_client()
    all_drugs = client.get_drugs()  # 通过HTTP调backend
    # 在客户端做症状匹配...
```

**改造后方式** — 筛选系统直接复用 Service：

```python
# P1 中引入 DrugServiceProtocol，不再走HTTP
from backend.services.drug_service import DrugServiceProtocol

class DrugScreeningService:
    def __init__(self, drug_service: DrugServiceProtocol):
        self.drug_service = drug_service

    def recommend(self, symptom: str):
        all_drugs = self.drug_service.search_by_name("")  # 复用Service
        # 专注做筛选业务逻辑，不关心数据从哪来
```

### 场景2：并行开发流程

| 时间 | 药品管理API同学 | 智能筛选同学 |
|------|----------------|-------------|
| 第1周结束 | 定义 `DrugRepositoryProtocol` | 定义 `DrugScreeningService` 接口 |
| 第2-3周 | 实现 `SqliteDrugRepository` | 自己写 `MockDrugRepository` 测试 |
| 第4周 | 完成后 → 通知筛选同学 | 替换 Mock → 真实 Repository |
| 接合点 | 只需要确认接口一致，几乎不会出问题 |

### 场景3：独立测试

**当前**：要测试 `list_drugs`，必须要有数据库和数据  
**改造后**：

```python
# 自己写一个假的 Repository 就能测试 Service 层
class FakeDrugRepo:
    def find_all(self):
        return [{"drug_id": 1, "name": "测试药", "quantity": 100}]
    def find_by_name(self, name):
        return [{"drug_id": 1, "name": "测试药", "quantity": 100}]

service = DrugService(FakeDrugRepo())
result = service.get_low_stock_drugs(threshold=50)
assert len(result) == 0  # 100 > 50，不应该返回
```

**不需要数据库，不需要启动Flask，几秒钟跑完测试。**

---

## 各层文件变化总结

| 目录 | 当前 | 改造后 |
|------|------|--------|
| `controllers/` | 混着SQL | 只调Service |
| `services/` | ❌不存在 | 新增：业务逻辑 + Protocol定义 |
| `repositories/` | ❌不存在 | 新增：数据访问 + Protocol实现 |
| `utils/database.py` | 完整SQL操作 | 只保留连接管理 |
| `P1/pharmacy_client.py` | 自己调HTTP | 改调 Service 接口 |

对已有代码的影响：最小化。现有 `controllers/` 只需要把 SQL 部分移到 `repositories/` 中，保留路由和参数解析逻辑。P1 中的 `pharmacy_client.py` 改为依赖接口，两端解耦。

---

## OpenAPI 规范说明

### 什么是 OpenAPI？

OpenAPI 是把 API 接口写在一个独立的 YAML/JSON 文件里，**谁都能读，不依赖代码**。它定义接口的参数、返回格式、错误码等，作为前后端之间的契约。

### 示例：用OpenAPI描述药品接口

```yaml
# api-spec.yaml
paths:
  /api/drugs:
    get:
      summary: 查询药品列表
      parameters:
        - name: name
          in: query
          description: 按名称筛选（支持模糊匹配）
          schema:
            type: string
          required: false
      responses:
        200:
          description: 成功返回药品列表
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  drugs:
                    type: array
                    items:
                      $ref: '#/components/schemas/Drug'
                  count:
                    type: integer
components:
  schemas:
    Drug:
      type: object
      properties:
        drug_id: { type: integer }
        name: { type: string }
        quantity: { type: integer }
        expiry_date: { type: integer }
```

### OpenAPI 带来的好处

**场景1：前后端并行开发**
- 前端同学拿到这个YAML文件，就可以用工具（如 Swagger Editor）**直接生成假数据**来调试界面
- 不需要等后端写完代码，也不需要翻后端代码找参数
- 后端按YAML实现，前端按YAML调用，接合时基本不会出错

**场景2：团队协作**
- 一个人改接口（比如"新增一个 `category` 参数"）→ 改这个YAML文件 → 所有人review
- 一旦YAML合并，每个人都清楚接口变没变
- 解决了分工方案里第一条风险："接口不一致"

**场景3：自动生成文档**
- 把这个YAML导入 Swagger UI，自动生成可交互的API文档页面
- 团队成员可以点按钮直接测试接口

---

## Protocol 说明

### 什么是 Protocol？

Protocol 是 Python 提供的一种**定义接口**的方式，类似于其他语言的 interface。它只声明"应该有什么方法"，不写具体实现。

```python
from typing import Protocol

class DrugService(Protocol):
    """药品查询服务 —— 智能筛选系统需要的功能"""
    def search_by_name(self, name: str) -> list[Drug]: ...
    def search_by_symptom(self, symptom: str) -> list[Drug]: ...
```

### 与团队分工的对应关系

| 团队成员 | OpenAPI 关系 | Protocol 关系 |
|----------|-------------|---------------|
| **前端开发** | 只看OpenAPI文件，知道调什么接口 | 不需要关心 |
| **药品管理API** | 负责实现OpenAPI中定义的端点 | 提供 `DrugService` 给其他模块用 |
| **智能筛选系统** | 可能新增筛选相关的API端点 | 依赖 `DrugService` Protocol，独立开发测试 |
| **权限认证系统** | 在OpenAPI中定义认证头、权限限制 | 提供 `AuthService` Protocol 给其他模块 |
| **数据库开发** | 确保数据模型与OpenAPI的Schema一致 | 实现 `Repository` Protocol 供API层调用 |

---

## Protocol 解决的问题

| 问题 | 解决前 | 解决后 |
|------|--------|--------|
| **依赖等待** | 筛选团队要等药品API写好才能测试 | 用Mock自己测，不需要等 |
| **改接口影响** | 药品API改了 → 筛选系统崩了才发现 | 改了Protocol → Python类型检查直接报错 |
| **模块耦合** | 筛选系统里混着HTTP调用代码 | 分工明确：筛选只管业务逻辑 |
