# AI 开药助手 —— 团队项目说明文档 ver 4.0

> **重要更新说明**：本文档基于项目实际状态完全重写，反映截至2026年4月8日的项目实现情况。与v3.0文档的主要差异包括：技术栈从FastAPI更改为Flask、API端点基于实际实现、角色完成状态标注等。

## 📋 更新摘要

### 主要变更
1. **技术栈更新**：实际使用Flask（非FastAPI）+ SQLite + ROS2
2. **项目结构更新**：基于实际目录结构，移除未实现的组件
3. **角色状态标注**：明确标注各角色完成状态（✅已完成/⚠️部分完成/❌未完成）
4. **API参考更新**：基于实际Flask API端点（`/api/*`）
5. **集成状态**：P1已通过HTTP API集成实际后端

### 文档版本历史
- **v1.0** (2025年3月) - 初始规划版本
- **v2.0** (2025年4月) - 基于learn-claude-code的模块化规划  
- **v3.0** (2026年4月) - 模块化架构规划（基于FastAPI）
- **v4.0** (2026年4月8日) - **当前版本**，基于实际项目状态重写

---


## 一、项目概述

### 1.1 项目名称
**ROS2-based Intelligent Medicine Pickup System**（ROS2智能药品拣选系统）

### 1.2 当前状态
- **开发阶段**：开发中
- **集成状态**：P1医疗助手与后端集成测试通过
- **最后更新**：2026年4月8日
- **代码仓库**：https://github.com/clouder1128/ROS2-based-Intelligent-Medicine-Pickup-System

### 1.3 核心价值
将AI医疗用药助手与智能药房管理系统结合，实现：患者症状咨询 → AI推荐药物 → 医生审批 → 自动配药 → ROS2机器人取药的完整闭环。

---

## 二、核心功能（已实现）

基于当前项目实际实现的核心功能：

| 功能模块 | 状态 | 技术实现 | 说明 |
|----------|------|----------|------|
| **智能药房管理** | ✅ 已实现 | `backend/app.py` + SQLite | 药品库存、有效期管理、货架定位、数据库操作 |
| **ROS2集成** | ✅ 已实现 | `backend/app.py` + rclpy | 取药任务发布到ROS2话题 `/task_request`，支持仿真系统（需配置ROS2环境） |
| **AI医疗助手** | ✅ 已实现 | `P1/core/agent.py` + LLM API | 症状分析、药品推荐、剂量计算、工具调用系统 |
| **医生审批流程** | ✅ 已实现 | `backend/approval.py` + Flask API | 完整的电子审批工作流，API端点：`/api/approvals/*` |
| **定时任务** | ✅ 已实现 | `backend/app.py` 后台线程 | 自动过期药品清扫，按日历推进的库存扣减 |
| **HTTP API集成** | ✅ 已实现 | `P1/utils/http_client.py` | P1通过HTTP API连接后端，支持异步/同步调用 |
| **完整测试套件** | ✅ 已实现 | `P1/tests/` + `backend/tests/` | 193个测试用例，100%通过 |

### 2.1 实际工作流程
1. **患者咨询** → P1医疗助手分析症状、查询药品
2. **AI推荐** → 调用`tools/medical.py`工具生成用药建议
3. **医生审批** → 通过`/api/approvals` API创建审批单
4. **审批处理** → 医生通过`/api/approvals/{id}/approve`批准
5. **自动配药** → 后端处理订单，扣减库存（未来集成药房仿真）
6. **ROS2任务** → 发布取药任务到仿真系统

### 2.2 与规划的主要差异
- **技术栈**：实际使用Flask（规划为FastAPI）
- **前端**：无独立前端界面（规划有5个HTML页面）
- **子代理**：无症状提取子代理（规划有`subagents/`）
- **规划器**：无TodoWrite规划器（规划有`planner.py`）

---

## 三、实际技术栈

### 3.1 后端服务
- **Web框架**: Flask（实际使用，非规划中的FastAPI）
- **数据库**: SQLite（`pharmacy.db`），直接使用sqlite3库操作
- **ROS2集成**: rclpy（可选，无ROS2时系统仍正常工作）
- **API风格**: RESTful HTTP API，默认端口8001（可通过`PORT`环境变量配置）
- **CORS支持**: flask_cors（开发环境配置为允许所有来源`*`，支持`GET/POST/PUT/DELETE/OPTIONS`方法）
- **定时任务**: Python threading（后台过期清扫，默认间隔3600秒，可通过`EXPIRY_SWEEP_INTERVAL_SEC`环境变量配置）
- **错误处理**: 完善的端口验证和错误回退机制
- **启动配置**: 支持调试模式和自动重载

### 3.2 AI医疗助手（P1模块）
- **核心框架**: 自定义MedicalAgent类（`P1/core/agent.py`）
- **LLM集成**: Claude/OpenAI/DeepSeek API（通过Anthropic兼容接口）
- **工具系统**: 标准化工具接口（`P1/tools/`目录）
- **消息管理**: 智能压缩和token估算（`P1/memory/`）
- **会话管理**: 状态保存和恢复（`P1/session/`）
- **HTTP客户端**: `PharmacyHTTPClient`（连接后端API，默认地址`http://localhost:8001`，可通过`PHARMACY_BASE_URL`环境变量配置）
- **错误处理**: 支持重试机制（默认3次重试，指数退避）
- **异步支持**: 同时支持同步和异步API调用

### 3.3 开发工具
- **版本控制**: Git + GitHub
- **测试框架**: pytest（193个测试用例）
- **依赖管理**: pip + requirements.txt
- **构建工具**: Makefile（一键启动、测试命令）
- **文档**: Markdown + 中文技术文档

### 3.4 与规划的技术差异
| 技术领域 | 规划 | 实际实现 | 差异说明 |
|----------|------|----------|----------|
| Web框架 | FastAPI | Flask | 实际使用更轻量级的Flask |
| 前端技术 | HTML/CSS/JS | 无独立前端 | 暂无前端界面，通过API调用 |
| 数据库ORM | SQLAlchemy（规划） | 直接SQLite3 | 简化实现，直接使用sqlite3 |
| 认证系统 | JWT/OAuth2（规划） | 无认证 | 开发环境无需认证 |
| 子代理系统 | 症状提取子代理 | 无子代理 | 症状分析集成在主Agent中 |

---

## 四、项目实际结构

```
agent/
├── backend/                    # ✅ 智能药房后端服务（Flask）
│   ├── app.py                 # Flask主应用（实际API端点）
│   ├── approval.py            # 审批管理模块（ApprovalManager类）
│   ├── init_db.py             # 数据库初始化脚本
│   ├── pharmacy.db           # SQLite数据库文件
│   ├── README.md              # 后端专属文档
│   └── tests/                 # 后端测试
│       ├── test_approval_api.py
│       └── test_drug_api.py
│
├── P1/                        # ✅ AI医疗助手系统
│   ├── core/                  # 核心模块
│   │   ├── agent.py           # MedicalAgent主类
│   │   └── workflows.py       # 工作流管理器
│   ├── llm/                   # LLM客户端
│   │   ├── client.py          # 统一LLM客户端
│   │   ├── schemas.py         # 数据模型
│   │   └── providers/         # LLM提供商实现
│   ├── tools/                 # 工具系统（⚠️ 部分mock）
│   │   ├── base.py            # 工具基类
│   │   ├── executor.py        # 工具执行器
│   │   ├── registry.py        # 工具注册表
│   │   ├── inventory.py       # 库存管理工具（✅ 集成后端）
│   │   ├── medical.py         # 医疗工具（⚠️ mock实现）
│   │   └── report_generator.py # 报告生成工具（⚠️ mock实现）
│   ├── utils/                 # 工具函数
│   │   ├── http_client.py     # HTTP客户端（✅ 集成后端）
│   │   └── ...                # 其他工具函数
│   ├── memory/                # 消息管理
│   ├── session/               # 会话管理
│   ├── tests/                 # 测试套件（193个用例）
│   └── README.md              # P1模块文档
│
├── scripts/                   # ✅ 实用脚本
│   ├── quick-start.sh         # 一键启动脚本
│   └── test-full-integration.py # 完整集成测试
│
├── docs/                      # ✅ 文档目录
│   ├── AI 开药助手 —— 团队项目说明文档 ver 3.0.md  # 旧版规划
│   ├── AI 开药助手 —— 团队项目说明文档 ver 4.0.md  # 当前文档（更新后）
│   ├── api-reference.md       # API参考（待整合）
│   ├── integration-guide.md   # 集成指南（待整合）
│   ├── troubleshooting.md     # 故障排除（待整合）
│   └── superpowers/           # 开发规划文档
│
├── tests/                     # ✅ 根目录测试
├── test/                      # ROS2仿真测试目录
├── Makefile                   # ✅ 项目构建工具
├── README.md                  # ✅ 项目主文档
└── .gitignore                 # Git忽略配置
```

**注意**：项目结构已优化，原`test/backend/`目录中的测试文件已整合到`backend/tests/`目录中，避免重复。`test/`目录仅保留ROS2仿真测试相关文件。

### 4.1 缺失的规划组件
- ❌ `api/`目录（规划中的FastAPI后端）
- ❌ `web/`目录（规划中的5个HTML页面）
- ❌ `subagents/`目录（规划中的症状提取子代理）
- ❌ `planner.py`文件（规划中的TodoWrite规划器）
- ❌ `audit_logger.py`文件（规划中的审计日志）

### 4.2 实际与规划的结构差异
1. **后端位置**：实际在`backend/`（Flask），规划在`api/`（FastAPI）
2. **前端缺失**：规划有完整前端，实际暂无独立前端界面
3. **工具状态**：部分工具为mock实现（`tools/medical.py`）
4. **审批模块**：实际在`backend/approval.py`，非独立`approval.py`

---

## 五、团队分工与完成状态（6人团队）

### 5.1 各角色实际完成状态

| 角色 | 规划代码量 | 实际状态 | 关键产出文件 | 完成度评估 |
|------|-----------|----------|--------------|-----------|
| **P1**<br>Agent核心工程师 | 1500行 | ✅ **已完成** | `P1/core/agent.py`<br>`P1/tools/registry.py`<br>`P1/llm/client.py`<br>`P1/memory/manager.py` | 实际代码量约2,000行，架构比规划更完善 |
| **P2**<br>医疗工具与知识库工程师 | 2900行 | ⚠️ **部分完成** | `P1/drug_db.py`（✅集成后端）<br>`P1/tools/inventory.py`（✅集成后端）<br>`P1/tools/medical.py`（⚠️ mock实现）<br>`P1/tools/report_generator.py`（⚠️ mock实现） | 数据库和库存工具已集成，医疗工具仍为mock |
| **P3**<br>规划与子代理工程师 | 1300行 | ❌ **未完成** | `planner.py`（❌不存在）<br>`subagents/`目录（❌不存在）<br>`task_storage.py`（❌不存在） | 规划器和子代理系统未实现 |
| **P4**<br>后端API工程师 | 2100行 | ⚠️ **完成但不同** | `backend/app.py`（✅ Flask实现）<br>`backend/approval.py`（✅ 审批模块）<br>`backend/init_db.py`（✅ 数据库初始化） | 技术栈不同（Flask vs FastAPI），API端点不同 |
| **P5**<br>前端工程师 | 3300行 | ❌ **未完成** | `web/`目录（❌不存在）<br>HTML/CSS/JS文件（❌不存在） | 前端界面未开发 |
| **P6**<br>测试/审批/集成工程师 | 1450行 | ⚠️ **部分完成** | `backend/approval.py`（✅ 已实现）<br>`backend/tests/`（✅ 测试存在）<br>`P1/tests/`（✅ 193个测试用例）<br>`audit_logger.py`（❌不存在）<br>`auth.py`（❌不存在） | 审批和测试已完成，审计日志和认证未完成 |

### 5.2 实际与规划的工作量对比

| 指标 | 规划 | 实际 | 差异分析 |
|------|------|------|----------|
| **总代码量** | 12,000行 | ≈8,500行 | 前端和部分模块未实现 |
| **P1实际代码** | 1,500行 | ≈2,000行 | 架构更完善，增加消息管理、会话管理等 |
| **测试覆盖率** | 规划>70% | 实际>80% | 测试更完善，193个测试用例100%通过 |
| **集成状态** | 规划集成 | ✅ 已集成 | P1与后端通过HTTP API完整集成 |

### 5.3 各角色详细任务状态

#### P1（Agent核心）✅ 已完成
- **实际完成**：MedicalAgent类、LLM客户端、工具注册系统、消息压缩、会话管理、工作流跟踪
- **超出规划**：增加了DeepSeek API支持、异步工具执行、智能消息压缩
- **测试状态**：核心功能测试完整，193个测试用例全部通过

#### P2（医疗工具）⚠️ 部分完成  
- **已完成**：`drug_db.py`（HTTP API集成）、`tools/inventory.py`（库存管理）
- **未完成**：`tools/medical.py`中的真实医疗逻辑（当前为mock）
- **关键差异**：`fill_prescription`工具仍为mock，未连接真实药房仿真系统

#### P3（规划子代理）❌ 未完成
- **缺失组件**：TodoWrite规划器、症状提取子代理、任务持久化
- **影响范围**：系统缺少规划能力，症状分析直接集成在Agent中
- **兼容性**：P1已实现条件导入，P3模块不存在时使用占位实现

#### P4（后端API）⚠️ 完成但不同
- **技术栈变更**：使用Flask（规划为FastAPI）
- **API端点差异**：实际端点`/api/*`（规划端点`/chat`、`/approve`等）
- **功能完整**：药品管理、订单处理、审批API、ROS2集成、定时任务全部实现

#### P5（前端）❌ 未完成
- **完全缺失**：无患者界面、医生界面、药房界面、历史查询、管理后台
- **替代方案**：当前通过命令行和API直接交互
- **优先级**：后端和AI功能优先，前端可后续开发

#### P6（测试审批）⚠️ 部分完成
- **已完成**：审批模块（`backend/approval.py`）、测试套件
- **未完成**：审计日志系统（`audit_logger.py`）、认证系统（`auth.py`）
- **测试质量**：测试覆盖率>80%，集成测试完整

---
### 5.4 实际开发时间线（调整后）

#### 已完成的里程碑
- **第0-1周**：项目初始化、架构设计、环境搭建 ✅
- **第1-2周**：P1 Agent核心开发完成 ✅
- **第2-3周**：后端Flask服务开发完成 ✅  
- **第3-4周**：P1与后端集成测试通过 ✅
- **第4-5周**：完整测试套件、文档更新 ✅

#### 待完成的工作
- **前端开发**：HTML/CSS/JS界面（P5负责）
- **医疗工具完善**：真实医疗逻辑实现（P2负责）
- **规划器实现**：TodoWrite规划系统（P3负责）
- **审计日志**：操作日志记录系统（P6负责）
- **药房仿真集成**：真实`fill_prescription`实现

#### 当前项目重点
1. **稳定现有功能**：确保P1与后端集成稳定运行
2. **完善文档**：更新文档反映实际状态（本文档）
3. **技术债务清理**：将mock工具替换为真实实现
4. **扩展规划**：按需开发前端和其他缺失功能

---

## 六、实际API参考（Flask后端）

### 6.1 基础信息
- **基础URL**: `http://localhost:8001`（开发环境）
- **认证**: 当前无认证，生产环境需实现API密钥或JWT
- **响应格式**: 所有响应为JSON，成功包含`"success": true`，错误包含`"error": true`
- **CORS**: 已配置支持跨域，前端可直接调用

### 6.2 实际API端点（`backend/app.py`）

#### 健康检查
```http
GET /api/health
```
**响应示例**:
```json
{
  "success": true,
  "backend": "pharmacy",
  "ros2_connected": false,
  "timestamp": "2026-04-07T10:30:00"
}
```

#### 药品管理
```http
GET /api/drugs
GET /api/drugs/{id}
```
**查询参数**: `name`（可选，按药品名称筛选）
**响应示例**:
```json
{
  "success": true,
  "drugs": [
    {
      "drug_id": 1,
      "name": "阿莫西林",
      "quantity": 50,
      "expiry_date": 365,
      "shelf_x": 1,
      "shelf_y": 1,
      "shelve_id": 1
    }
  ],
  "count": 1
}
```

#### 审批管理
```http
POST /api/approvals                    # 创建审批
GET /api/approvals/{id}               # 获取审批详情  
GET /api/approvals/pending            # 获取待审批列表
POST /api/approvals/{id}/approve      # 批准审批
POST /api/approvals/{id}/reject       # 拒绝审批
```

**创建审批请求体**:
```json
{
  "patient_name": "John Doe",
  "advice": "Take medication",
  "patient_age": 30,
  "patient_weight": 70.5,
  "symptoms": "Headache",
  "drug_name": "Ibuprofen",
  "drug_type": "NSAID"
}
```

#### 订单管理
```http
POST /api/order                       # 批量取药（主要接口）
POST /api/pickup                      # 单条取药（兼容接口）
GET /api/orders                       # 获取订单历史
```

**批量取药请求体**:
```json
[
  {"id": 1, "num": 2},
  {"id": 2, "num": 1}
]
```

### 6.3 与规划API的差异映射

| 规划端点 | 实际端点 | 差异说明 |
|----------|----------|----------|
| `POST /chat` | ❌ 未实现 | 聊天功能集成在P1 Agent中，无独立HTTP端点 |
| `POST /approve` | `POST /api/approvals/{id}/approve` | 实际端点更规范，包含审批ID |
| `GET /pending` | `GET /api/approvals/pending` | 功能相同，路径不同 |
| `GET /prescription/{id}` | ❌ 未实现 | 处方查询未独立实现，在审批中处理 |
| `GET /admin/*` | ❌ 未实现 | 管理功能通过数据库直接操作 |
| `GET /history` | ❌ 未实现 | 历史查询未实现 |

### 6.4 P1 API客户端使用示例

```python
from P1.utils.http_client import PharmacyHTTPClient

# 初始化客户端（自动读取PHARMACY_BASE_URL环境变量）
client = PharmacyHTTPClient()

# 获取所有药品
drugs = client.get_drugs()

# 创建审批
approval_id = client.create_approval(
    patient_name="张三",
    advice="按时服药，多休息",
    symptoms="头痛、发热"
)

# 批量取药
order_result = client.create_order([
    {"id": 1, "num": 2},  # 药品ID 1，数量2
    {"id": 2, "num": 1}   # 药品ID 2，数量1
])
```

---
## 七、实际开发工作流程

### 7.1 环境准备
```bash
# 1. 克隆项目
git clone https://github.com/clouder1128/ROS2-based-Intelligent-Medicine-Pickup-System.git
cd ROS2-based-Intelligent-Medicine-Pickup-System

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt
python init_db.py  # 初始化数据库

# 3. 安装P1依赖
cd ../P1
pip install -r requirements.txt

# 4. 设置环境变量
export PHARMACY_BASE_URL=http://localhost:8001
```

### 7.2 日常开发流程

#### 启动服务
```bash
# 终端1：启动后端服务（端口8001）
make backend-start

# 终端2：运行P1 CLI（需要先设置PHARMACY_BASE_URL）
cd P1
python cli.py
```

#### 运行测试
```bash
# 运行P1单元测试（mock后端）
make test

# 运行完整集成测试（需要后端运行）
make test-integration

# 运行特定测试模块
cd P1 && pytest tests/test_drug_db_simple.py -v
```

#### 调试工具
```bash
# 查看后端日志
cd backend && python app.py

# 启用调试日志
export LOG_LEVEL=DEBUG

# 直接测试API
curl http://localhost:8001/api/health
curl http://localhost:8001/api/drugs
```

### 7.3 项目构建命令（Makefile）
```bash
make quick-start          # 一键启动（后端+P1）
make backend-start        # 仅启动后端
make test                # 运行P1单元测试
make test-integration    # 运行集成测试
make clean              # 清理临时文件
```

### 7.4 数据库管理
```bash
# 初始化/重置数据库
cd backend && python init_db.py

# 直接查询数据库
sqlite3 backend/pharmacy.db "SELECT * FROM inventory;"

# 备份数据库
cp backend/pharmacy.db backend/pharmacy.db.backup
```

---

## 八、安全注意事项

### 8.1 API密钥安全（关键）
**重要原则**：永远不要将真实API密钥提交到版本控制系统！

#### 正确做法
1. **使用`.env`文件**管理敏感信息
2. **`.env`必须在`.gitignore`中**
3. **提交`.env.example`**作为模板
4. **代码中从环境变量读取**API密钥

#### 环境变量配置
```bash
# .env.example（模板文件）
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
PHARMACY_BASE_URL=http://localhost:8001
LOG_LEVEL=INFO

# 代码中读取
from config import Config
api_key = Config.ANTHROPIC_API_KEY
```

#### 安全检查清单
```bash
# 检查本地环境
cd /home/clouder/agent
if [ -f ".env" ]; then
    echo "✅ 发现.env文件"
    if git check-ignore .env >/dev/null; then
        echo "✅ .env已在.gitignore中"
    else
        echo "❌ .env未在.gitignore中，请立即修复！"
    fi
else
    echo "⚠️ 未找到.env文件，请从.env.example创建"
fi
```

### 8.2 生产环境安全建议
1. **API认证**：实现API密钥或JWT认证
2. **输入验证**：所有API端点验证输入数据
3. **SQL注入防护**：使用参数化查询（当前已实现）
4. **CORS限制**：生产环境限制允许的源
5. **日志脱敏**：日志中不记录敏感信息
6. **定期更新**：保持依赖库更新到安全版本

### 8.3 应急响应
1. **API密钥泄露**：立即轮换所有相关密钥
2. **数据库损坏**：从备份恢复，检查日志
3. **服务不可用**：检查日志，重启服务，联系维护人员

---
## 九、附录

### 9.1 常用命令速查
```bash
# 健康检查
curl http://localhost:8001/api/health

# 获取药品列表
curl http://localhost:8001/api/drugs

# 创建审批
curl -X POST http://localhost:8001/api/approvals \
  -H "Content-Type: application/json" \
  -d '{"patient_name":"测试","advice":"测试建议"}'

# 运行完整测试套件
cd P1 && pytest tests/ -v

# 查看服务日志
cd backend && tail -f nohup.out
```

### 9.2 故障排除快速参考
1. **端口冲突**：检查端口8001是否被占用 `sudo lsof -i :8001`
2. **连接失败**：验证`PHARMACY_BASE_URL`环境变量
3. **数据库锁定**：检查其他进程是否使用`pharmacy.db`
4. **导入错误**：确保所有依赖已安装 `pip install -r requirements.txt`

### 9.3 获取帮助
1. **项目仓库**：https://github.com/clouder1128/ROS2-based-Intelligent-Medicine-Pickup-System
2. **文档目录**：`docs/`（包含本文档和技术参考）
3. **测试套件**：`P1/tests/` 和 `backend/tests/`
4. **问题反馈**：通过GitHub Issues报告问题

### 9.4 版本更新记录

#### v4.0（2026年4月8日） - 当前版本
- **完全重写**：基于实际项目状态更新所有内容
- **状态标注**：明确标注各角色完成状态
- **技术准确**：基于实际Flask API和项目结构
- **API更新**：使用实际端点，移除未实现的规划端点
- **安全整合**：包含API密钥安全指南

#### v3.0（2026年4月） - 上一版本
- 基于模块化架构规划（FastAPI + 前端 + 子代理）
- 包含完整的6人团队分工和12000行代码规划
- 技术栈：FastAPI + HTML/CSS/JS + SQLite

#### v2.0（2025年4月） - 早期版本
- 基于learn-claude-code复制粘贴的规划
- 基础Agent循环和工具调用框架

#### v1.0（2025年3月） - 初始版本
- 项目概念和基础规划

---

## 📞 联系方式

- **项目维护**：P1模块负责人
- **代码仓库**：https://github.com/clouder1128/ROS2-based-Intelligent-Medicine-Pickup-System
- **文档更新**：本文档应随项目进展定期更新
- **问题反馈**：发现文档与实际不符时请及时报告

---

**最后更新：2026年4月8日**  
**文档状态：v4.0（当前版本）**  
**项目状态：开发中 - P1与后端集成测试通过**

> **重要提示**：本文档基于项目实际状态编写，与v3.0文档存在显著差异。使用前请仔细阅读"更新摘要"和"规划与实际差异"部分。




