# Backend to P1 Integration Analysis

## 1. 项目概述

本文档详细分析 `backend/` 目录下的智能取药系统后端，并提供将其集成到 P1 医疗用药助手 Agent 系统中的建议方案。

**核心需求**：保留 backend 的 ROS2 和定时任务功能，用于未来接入仿真系统。

## 2. Backend 功能详细分析

### 2.1 系统架构

```
┌─────────────────────────────────────────────┐
│              Backend (Flask 服务)           │
├─────────────────────────────────────────────┤
│  • Flask API (端口5000)                    │
│  • SQLite 数据库 (pharmacy.db)             │
│  • ROS2 集成 (可选)                        │
│  • 定时任务 (过期清扫)                     │
│  • 审批管理 (Python模块)                   │
└─────────────────┬───────────────────────────┘
                  │
          HTTP API│ROS2话题
                  │
┌─────────────────▼───────────────────────────┐
│               外部系统                       │
│  • P1医疗助手 (HTTP客户端)                  │
│  • 仿真系统 (ROS2订阅者)                    │
│  • 前端界面 (HTML/JS)                       │
└─────────────────────────────────────────────┘
```

### 2.2 数据库结构

#### 2.2.1 `inventory` 表 (药品库存)
| 字段 | 类型 | 说明 |
|------|------|------|
| drug_id | INTEGER PRIMARY KEY | 药品ID |
| name | TEXT NOT NULL | 药品名称 |
| quantity | INTEGER NOT NULL | 库存数量 |
| expiry_date | INTEGER NOT NULL | 剩余天数（≤0表示已过期）|
| shelf_x | INTEGER NOT NULL | 货架X坐标 |
| shelf_y | INTEGER NOT NULL | 货架Y坐标 |
| shelve_id | INTEGER NOT NULL | 货架ID |

#### 2.2.2 `order_log` 表 (取药记录)
| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | INTEGER PRIMARY KEY AUTOINCREMENT | 任务ID |
| status | TEXT NOT NULL | 状态（pending等） |
| target_drug_id | INTEGER | 目标药品ID |
| quantity | INTEGER | 取药数量 |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 2.2.3 `app_meta` 表 (应用元数据)
| 字段 | 类型 | 说明 |
|------|------|------|
| k | TEXT PRIMARY KEY | 键 |
| v | TEXT NOT NULL | 值 |

**关键数据**：`expiry_sweep_date` - 过期清扫基准日，用于按日历推进有效期扣减。

#### 2.2.4 `approvals` 表 (医生审批单)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PRIMARY KEY | 审批单ID（格式：AP-YYYYMMDD-XXXXXXXX） |
| patient_name | TEXT NOT NULL | 患者姓名 |
| patient_age | INTEGER | 患者年龄 |
| patient_weight | REAL | 患者体重 |
| symptoms | TEXT | 症状描述 |
| advice | TEXT NOT NULL | 用药建议 |
| drug_name | TEXT | 药品名称 |
| drug_type | TEXT | 药品类型 |
| status | TEXT NOT NULL | 状态（pending/approved/rejected） |
| doctor_id | TEXT | 医生ID |
| reject_reason | TEXT | 拒绝原因 |
| created_at | DATETIME DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| approved_at | DATETIME | 审批时间 |

### 2.3 核心功能模块

#### 2.3.1 Flask API 服务 (`app.py`)
**主要端点：**
- `GET /api/health` - 健康检查（含ROS2连接状态）
- `GET /api/drugs` - 列出所有药品
- `GET /api/orders` - 查看取药记录（最近50条）
- `POST /api/order` - 批量取药（主要接口）
- `POST /api/pickup` - 单条取药（兼容接口）

**关键特性：**
- CORS支持：允许前端跨域访问
- 事务处理：下单时库存扣减与订单记录原子操作
- ROS2集成：发布任务到 `/task_request` 话题
- 错误处理：返回标准JSON错误响应

#### 2.3.2 过期清扫系统
**工作原理：**
1. **定时任务**：后台线程每3600秒检查一次（可通过`EXPIRY_SWEEP_INTERVAL_SEC`调整）
2. **按日历推进**：基于`app_meta.expiry_sweep_date`计算天数差，一次性扣减
3. **过期处理**：过期药品数量置0，发布ROS2清柜任务
4. **防重复**：同一自然日只执行一次扣减

**ROS2消息格式：**
```json
// 用户取药
{
  "task_id": 1,
  "type": "pickup",
  "drug_id": 1,
  "name": "阿莫西林",
  "shelve_id": 1,
  "x": 1,
  "y": 1,
  "quantity": 2
}

// 过期清柜
{
  "task_id": null,
  "type": "expiry_removal",
  "drug_id": 1,
  "name": "阿莫西林",
  "shelve_id": 1,
  "x": 1,
  "y": 1,
  "quantity": 10,
  "reason": "expired"
}
```

#### 2.3.3 审批管理系统 (`approval.py`)
**核心类：** `ApprovalManager`
- **状态管理**：`pending` → `approved`/`rejected`
- **ID生成**：`AP-YYYYMMDD-XXXXXXXX` 格式
- **线程安全**：使用锁保证并发安全
- **单例模式**：通过`get_approval_manager()`获取

**主要方法：**
- `create()` - 创建审批单
- `get()` - 查询审批单
- `list_pending()` - 查询待审批列表
- `approve()` - 批准审批单
- `reject()` - 拒绝审批单

**注意**：当前backend未暴露审批HTTP接口，仅为Python模块。

#### 2.3.4 数据库初始化 (`init_db.py`)
**功能：**
- 创建数据库表结构
- 插入示例药品数据
- 设置过期清扫基准日为当天
- 清空已有数据（重置状态）

### 2.4 启动与配置

#### 2.4.1 启动方式
```bash
# 1. 初始化数据库
python3 init_db.py

# 2. 启动服务
python3 app.py  # 监听 http://0.0.0.0:5000
```

#### 2.4.2 环境变量
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EXPIRY_SWEEP_INTERVAL_SEC` | 3600 | 过期清扫间隔（秒） |
| `APPROVAL_DB_PATH` | `./pharmacy.db` | 审批数据库路径 |
| ROS2相关 | 自动检测 | ROS2库存在时启用 |

#### 2.4.3 部署注意事项
- **Flask重载**：使用`flask run`或`python app.py`时注意定时线程的启动
- **ROS2依赖**：需要`rclpy`和`std_msgs`包，ROS2环境需先source
- **数据库路径**：默认使用相对路径`pharmacy.db`

## 3. P1 现状分析

### 3.1 项目结构
P1是一个医疗用药助手Agent系统，当前处于**占位实现**阶段：

```
P1/
├── drug_db.py              # 药品数据库（mock）
├── tools/
│   ├── medical.py         # 医疗工具（mock，含submit_approval）
│   └── inventory.py       # 库存管理（mock）
├── config.py              # 配置（已有PHARMACY_BASE_URL）
├── core/agent.py          # MedicalAgent主类
└── core/workflows.py      # 工作流管理（含SUBMIT_APPROVAL步骤）
```

### 3.2 需要替换的mock功能

#### 3.2.1 `drug_db.py`（药品数据库）
**当前状态**：返回硬编码的mock药品数据
**需实现的功能**：
- `query_drugs_by_symptom(symptom)` - 按症状查询药品
- `query_drug_by_name(name)` - 按名称查询药品
- `update_stock(drug_id, quantity, type)` - 更新库存
- `get_all_drugs()` - 获取所有药品

#### 3.2.2 `tools/medical.py`（医疗工具）
**关键mock函数**：
- `query_drug(query)` - 药品查询（使用mock数据库）
- `submit_approval(...)` - 提交审批（生成mock审批ID）
- `check_allergy(...)` - 过敏检查（mock）

#### 3.2.3 `tools/inventory.py`（库存管理）
**mock功能**：
- `record_transaction(...)` - 记录库存流水
- `get_stock_report(...)` - 获取库存报告
- `generate_purchase_suggestions()` - 生成采购建议

### 3.3 现有配置
**`config.py` 关键配置：**
```python
PHARMACY_BASE_URL = os.getenv("PHARMACY_BASE_URL", "http://localhost:8001")
```
说明P1原本就设计为通过HTTP API与外部药房服务通信。

### 3.4 工作流状态
P1的工作流管理器已定义审批步骤：
```python
class WorkflowStep(Enum):
    SUBMIT_APPROVAL = "submit_approval"  # 提交审批
```

MedicalAgent在执行过程中会调用`submit_approval`工具，并记录`approval_id`。

## 5. 推荐方案：API服务集成

### 5.1 架构设计
```
┌─────────────────┐     HTTP API     ┌─────────────────┐
│                 │◄────────────────►│                 │
│   P1 Medical    │   (端口8001)     │   Backend       │
│    Assistant    │                  │  (Pharmacy)     │
│                 │                  │                 │
│  • 医疗Agent    │                  │  • Flask API    │
│  • 工具系统     │                  │  • 数据库       │
│  • 工作流管理   │                  │  • ROS2桥接     │
│  • LLM客户端    │                  │  • 定时任务     │
└─────────────────┘                  └─────────────────┘
```

### 5.2 Backend需要扩展的功能

#### 5.2.1 审批API端点（当前缺失）
需要在`app.py`中添加以下路由：
- `POST /api/approvals` - 创建审批单
- `GET /api/approvals/<approval_id>` - 查询审批单
- `POST /api/approvals/<approval_id>/approve` - 批准
- `POST /api/approvals/<approval_id>/reject` - 拒绝
- `GET /api/approvals/pending` - 待审批列表

这些端点应包装现有的`ApprovalManager`功能。

#### 5.2.2 药品查询增强
- 支持按症状过滤（可在客户端或服务端实现）
- 支持分页和搜索参数

#### 5.2.3 配置修改
- 端口从5000改为8001（匹配P1的`PHARMACY_BASE_URL`）
- 增强CORS配置，允许P1前端访问

### 5.3 P1改造点

#### 5.3.1 `drug_db.py` 改造
**现状**：
```python
def query_drugs_by_symptom(symptom: str) -> List[Dict]:
    # 返回mock数据
    return mock_drugs
```

**目标**：
```python
def query_drugs_by_symptom(symptom: str) -> List[Dict]:
    # HTTP调用 backend /api/drugs
    # 客户端按症状过滤，或backend支持症状参数
    response = httpx.get(f"{PHARMACY_BASE_URL}/api/drugs")
    drugs = response.json()
    # 过滤逻辑...
    return filtered_drugs
```

#### 5.3.2 `tools/medical.py` 改造
**关键函数**：`submit_approval`
```python
def submit_approval(patient_name: str, advice: str, **kwargs) -> str:
    # 调用 POST /api/approvals
    payload = {
        "patient_name": patient_name,
        "advice": advice,
        # ...其他参数
    }
    response = httpx.post(f"{PHARMACY_BASE_URL}/api/approvals", json=payload)
    result = response.json()
    return result["approval_id"]
```

#### 5.3.3 统一HTTP客户端
- 使用`httpx`库（P1已依赖）
- 配置超时、重试、错误处理
- 添加请求日志和监控

### 5.4 数据流示例

**完整用药咨询流程：**
1. 患者向P1描述症状："头痛、发烧"
2. P1调用`query_drugs_by_symptom("头痛 发烧")`
3. Backend返回相关药品列表
4. P1 LLM生成用药建议："建议服用布洛芬200mg"
5. P1调用`submit_approval()`创建审批单
6. 医生通过界面审批（调用backend的审批API）
7. 审批通过后，P1调用`/api/order`下单
8. Backend扣减库存，发布ROS2取药任务
9. 仿真系统执行取药操


## 7 未来扩展
1. **认证授权**：为API添加认证机制（JWT/OAuth2）
2. **负载均衡**：Backend多实例部署
3. **数据库扩展**：迁移到PostgreSQL/MySQL
4. **消息队列**：使用消息队列解耦ROS2任务发布




**文档信息**
- **创建时间**：2026年4月7日
- **文档状态**：分析完成，等待决策
- **注意事项**：本文档仅提供分析和建议，不包含实际代码修改
