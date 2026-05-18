# ROS2智能药品拣选系统 - Agent与后端集成

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-API-brightgreen)

集成的智能药品拣选系统，结合AI医疗助手与自动化药房后端，实现从医疗咨询到机器人取药的完整工作流。

## 目录

- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API概览](#api概览)
- [开发配置](#开发配置)
- [测试指南](#测试指南)

## 核心特性

### AI医疗助手
- **智能医疗咨询**：症状分析、药品推荐、剂量计算、多药联用
- **多LLM提供商**：支持 OpenAI、Claude 等主流 LLM API
- **药品数据库**：内置 116 种药品（12 大类，599 条适应症），支持症状→药品智能匹配
- **同义词扩展**：30 条症状同义词映射 + LLM 同义词重试，提高查询召回率
- **标准 Tool Call 协议**：消息格式遵循 OpenAI 标准，兼容多模型供应商

### 自动化药房后端
- **REST API 服务**：药品管理、订单处理、审批流程完整 API
- **库存管理**：实时库存跟踪、有效期管理、过期药品自动清理
- **审批流程**：完整电子审批，医生审批后自动触发取药

## 系统架构

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   AI Medical    │◄───────────────│  Smart Pharmacy │
│   Assistant     │   (8001端口)   │   Backend       │
│                 │                │                 │
│  • LLM Agent    │                │  • Flask API    │
│  • Medical Tools│                │  • SQLite DB    │
│  • Workflows    │                │  • Timed Tasks  │
│  • Memory       │                │                 │
│  • Sub-agents   │                │                 │
└────────┬────────┘                └────────┬────────┘
         │                                   │ ROS2 (可选)
         │                                   │ /task_request
   用户咨询                             机器人取药
```

### 工作流

1. 用户描述症状 → 症状提取子代理结构化提取
2. 系统按适应症批量查询药品（3 层：直接匹配→同义词→LLM 重试）
3. LLM Agent 根据药品列表筛选、检查过敏、计算剂量、多药联用
4. 生成用药建议 → 提交医生审批 → 等待审批结果
5. 审批通过 → 更新库存

## 快速开始

### 环境要求

- Python 3.8+
- 至少一个 LLM API 密钥（OpenAI / Claude）

### 安装与启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，设置 LLM 相关配置

# 3. 初始化数据库（建表 + 种子数据）
python database/scripts/init_db.py
python database/scripts/seed_drugs.py

# 4. 启动后端服务（端口 8001）
python main.py

# 5. 启动交互式 CLI
python cli/patient_cli.py
```

### 验证步骤

```bash
# 验证后端健康状态
curl http://localhost:8001/api/health

# 验证药品查询（URL编码：头痛 = %E5%A4%B4%E7%97%9B）
curl "http://localhost:8001/api/drugs?symptom=%E5%A4%B4%E7%97%9B"

# 验证同义词扩展（脑袋疼 → 头痛）
curl "http://localhost:8001/api/drugs?symptom=%E8%84%91%E8%A2%8B%E7%96%BC"

# 验证 CLI 端到端工作流
python cli/patient_cli.py test_patient
# 输入: 老王,30岁,60kg,轻度头疼,无过敏历史
# 预期: 完整执行 5 步 → 获取审批 ID
```

## 项目结构

```
agent_with_backend/
├── agent/                        # AI 医疗助手核心
│   ├── engine/                   # Agent 引擎
│   │   ├── medical_agent.py      # MedicalAgent 主类（Agent循环、状态管理）
│   │   └── workflows.py          # 工作流状态枚举与管理器
│   ├── llm/                      # LLM 客户端
│   │   ├── client.py             # 统一客户端（支持流式/非流式）
│   │   ├── schemas.py            # LLMMessage、ToolCall 等数据模型
│   │   └── providers/            # 提供商适配
│   │       └── openai.py         # OpenAI兼容API（含 SSE tool_call 回退解析）
│   ├── memory/                   # 对话记忆管理
│   │   ├── manager.py            # MessageManager（自动压缩与截断）
│   │   └── compressor.py         # 智能压缩
│   ├── subagents/                # 子代理
│   │   ├── extractor.py          # 症状提取（规则+LLM双模式，程度词剥离）
│   │   ├── models.py             # StructuredSymptoms、PatientInfo 模型
│   │   └── api.py                # 提取函数入口
│   └── tools/                    # 工具系统
│       ├── registry.py           # 工具注册表与 TOOLS schema
│       ├── executor.py           # 工具执行器
│       └── medical.py            # 医疗工具（query_drug, check_allergy, calc_dosage 等）
│
├── api/                          # Flask API 控制器
│   ├── drug_controller.py        # 药品 API（支持 symptom 查询参数）
│   ├── approval_controller.py    # 审批 API
│   ├── order_controller.py       # 订单 API
│   └── health_controller.py      # 健康检查
│
├── database/                     # 数据库层
│   ├── connection.py             # 数据库连接管理
│   ├── pharmacy_client.py        # 药品数据 HTTP 客户端
│   ├── pharmacy.db               # SQLite 数据库文件
│   ├── models/
│   │   └── drug.py               # Drug 数据模型
│   ├── scripts/
│   │   ├── init_db.py            # 建表脚本（含新表创建）
│   │   └── seed_drugs.py         # 116 种药品种子数据
│   └── approval_manager.py       # 审批管理
│
├── common/                       # 通用模块
│   ├── config.py                 # 全局配置（环境变量）
│   ├── exceptions.py             # 异常定义
│   └── utils/
│       ├── database.py           # 数据库工具
│       ├── http_client.py        # HTTP 客户端
│       └── json_tools.py         # JSON 工具
│
├── cli/                          # 命令行界面
│   ├── patient_cli.py            # 患者交互 CLI
│   └── doctor_cli.py             # 医生审批 CLI
│
├── main.py                       # Flask 主入口
└── pharmacy.db                   # 数据库文件
```

## API 概览

### 健康检查
- `GET /api/health` — 系统健康状态

### 药品管理
- `GET /api/drugs` — 获取药品列表
  - `?symptom=头痛` — 按适应症查询（支持同义词扩展：脑袋疼→头痛）
  - `?name=阿莫西林` — 按名称查询
- `GET /api/drugs/<id>` — 获取单个药品详情

### 订单处理
- `GET /api/orders` — 取药记录
- `POST /api/order` — 批量取药

### 审批流程
- `POST /api/approvals` — 创建审批单
- `GET /api/approvals/<id>` — 查询审批状态
- `GET /api/approvals/pending` — 待审批列表
- `POST /api/approvals/<id>/approve` — 批准审批
- `POST /api/approvals/<id>/reject` — 拒绝审批

### 药品查询三层匹配流程

```
用户症状（如"脑袋疼"）
    │
    ├─ 第一层：直接查 drug_indications
    │   LIKE '%脑袋疼%' → 无匹配
    │
    ├─ 第二层：查 symptom_synonyms 同义词表
    │   synonym='脑袋疼' → standard_term='头痛'
    │   → 用"头痛"查 drug_indications → 找到药品
    │
    └─ 第三层（Agent 内部）：LLM 生成同义词重试
        最多 3 次，仍空 → 建议就医
```

## 开发配置

关键环境变量（`.env`）：

```bash
# LLM 配置
LLM_PROVIDER=openai             # 提供商：openai / claude
OPENAI_API_KEY=sk-your-key      # API 密钥
OPENAI_BASE_URL=                # 可选：兼容 API 地址
LLM_MODEL=glm-4-flash           # 模型名
LLM_TEMPERATURE=0.3             # 温度（默认 0.3）

# 服务器配置
HOST=0.0.0.0
PORT=8001

# Agent 配置
MAX_ITERATIONS=15               # 最大循环次数
MAX_HISTORY_LEN=20              # 对话历史长度
ENABLE_LLM_SYMPTOM_EXTRACTION=true  # 启用 LLM 症状提取

# 思考记录（调试用）
ENABLE_THOUGHT_LOGGING=false
THOUGHT_LOG_DIR=./logs/thoughts
```

## 测试指南

### 端到端工作流测试（经验证通过）

输入 `"老王,30岁,60kg,轻度头疼,无过敏历史"`：

```
步骤1: query_drug("头疼")    → 返回药品列表（布洛芬、对乙酰氨基酚等）
步骤2: check_allergy("无", "布洛芬") → 无过敏风险
步骤3: calc_dosage("布洛芬", 30岁, 60kg) → 推荐剂量
步骤4: generate_advice("布洛芬", "500mg 每8小时一次") → 用药建议
步骤5: submit_approval(...)  → 返回审批 ID ✓
```

**当前 Agent 可顺利完成完整工作流**（5 步工具调用），经端到端测试验证可获取审批 ID。

### 边缘场景

| 场景 | 预期行为 |
|------|---------|
| 轻度头疼 | 症状提取为"头疼"，程度记录为"轻度" |
| 青霉素过敏 | 排除阿莫西林等青霉素类药品 |
| 头痛发热 | 匹配两种症状的药品，支持多药联用 |
| 无匹配症状（3 次重试后） | 建议就医 |
| 特殊字符 | API 正常拦截 |

### 数据库初始化验证

```bash
python3 -c "
import sqlite3
from common.config import Config
conn = sqlite3.connect(Config.DATABASE_PATH)
print('inventory:', conn.execute('SELECT COUNT(*) FROM inventory').fetchone()[0], 'rows')
print('indications:', conn.execute('SELECT COUNT(*) FROM drug_indications').fetchone()[0], 'rows')
print('synonyms:', conn.execute('SELECT COUNT(*) FROM symptom_synonyms').fetchone()[0], 'rows')
conn.close()
"
# 预期输出:
#   inventory: 116 rows
#   indications: 599 rows
#   synonyms: 30 rows
```

---

*最后更新：2026年4月25日*
*当前 Agent 状态：工作流可顺利运行*
