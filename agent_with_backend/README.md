# ROS2智能药品拣选系统 - Agent与后端集成

![ROS2 Jazzy](https://img.shields.io/badge/ROS2-Jazzy-blue)
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-API-brightgreen)

集成的智能药品拣选系统，结合AI医疗助手与ROS2自动化药房后端，实现从医疗咨询到机器人取药的完整工作流。

## 📖 目录
- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API概览](#api概览)
- [开发工作流](#开发工作流)
- [测试指南](#测试指南)

## 🧪 项目简介

智能药品拣选系统包含两大组件：
1. **P1医疗助手** - 基于LLM的AI代理，提供症状分析、药品推荐、剂量计算等医疗咨询服务
2. **智能药房后端** - Flask REST API服务，管理药品库存、处理订单、集成ROS2机器人控制

系统支持完整的电子审批流程，医生审批后自动触发机器人取药任务。

## ⚡ 核心特性

### P1医疗助手
- **智能医疗咨询**：症状分析、药品推荐、剂量计算
- **多LLM提供商**：支持Claude、OpenAI、DeepSeek等主流LLM API
- **模块化工具系统**：标准化工具调用接口，支持异步/同步执行
- **工作流管理**：跟踪患者咨询状态，支持会话保存/恢复

### 智能药房后端
- **REST API服务**：提供药品管理、订单处理、审批流程等完整API
- **ROS2集成**：自动化发布取药任务到仿真系统
- **库存管理**：实时库存跟踪、有效期管理、过期药品自动清理
- **定时任务**：后台线程处理过期药品清扫和库存维护

## 🏗️ 系统架构

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   P1 Medical    │◄───────────────│   Smart Pharmacy│
│    Assistant    │   (8001端口)   │    Backend      │
│                 │                │                 │
│  • LLM Agent    │                │  • Flask API    │
│  • Medical Tools│                │  • SQLite DB    │
│  • Workflows    │                │  • ROS2 Bridge  │
│  • Memory       │                │  • Timed Tasks  │
└────────┬────────┘                └────────┬────────┘
         │                                   │ ROS2
         │                                   │ /task_request
   用户咨询                               机器人取药
```

**数据流**：
1. 用户咨询症状 → P1医疗助手分析
2. P1查询后端药品信息 → 生成用药建议
3. 提交医生审批 → 等待审批结果
4. 审批通过 → 后端发布ROS2取药任务
5. 机器人执行取药 → 更新库存状态

## 🚀 快速开始

### 环境要求
- Python 3.8+
- ROS2 Jazzy（可选，仅ROS2集成需要）
- 至少一个LLM API密钥（DeepSeek/Claude/OpenAI）

### 后端启动
```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python init_db.py

# 4. 启动服务（默认端口8001）
python main.py
```

### P1医疗助手启动
```bash
# 1. 进入P1目录
cd P1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件，设置API密钥和PHARMACY_BASE_URL

# 4. 启动交互式CLI
python cli/doctor_cli.py
```

### 集成验证
```bash
# 验证后端健康状态
curl http://localhost:8001/api/health

# 验证P1与后端连接
cd P1
python -c "from services import pharmacy_client; print(pharmacy_client.health_check())"
```

## 📁 项目结构

```
agent_with_backend/
├── backend/                    # 智能药房后端
│   ├── main.py                # Flask主应用
│   ├── controllers/           # API控制器
│   │   ├── drug_controller.py     # 药品API
│   │   ├── order_controller.py    # 订单API
│   │   ├── approval_controller.py # 审批API
│   │   └── health_controller.py   # 健康检查
│   ├── models/                # 数据模型
│   │   ├── drug.py           # 药品模型
│   │   ├── order.py          # 订单模型
│   │   └── approval.py       # 审批模型
│   ├── ros_integration/      # ROS2集成模块
│   │   ├── task_publisher.py     # 任务发布器
│   │   ├── state_subscriber.py   # 状态订阅器
│   │   ├── message_adapter.py    # 消息适配器
│   │   └── health_monitor.py     # 健康监控
│   ├── utils/                # 工具函数
│   │   ├── database.py       # 数据库操作
│   │   ├── logger.py         # 日志配置
│   │   └── ros2_bridge.py    # ROS2桥接工具
│   ├── pharmacy.db          # SQLite数据库文件
│   └── tests/               # 后端测试
│
├── P1/                       # 医疗助手系统
│   ├── core/                # 核心模块
│   │   ├── agent.py         # MedicalAgent主类
│   │   ├── workflows.py     # 工作流管理器
│   │   └── config.py        # 配置管理
│   ├── tools/               # 工具系统
│   │   ├── registry.py      # 工具注册表
│   │   ├── base.py          # 工具基类
│   │   ├── medical.py       # 医疗工具
│   │   └── inventory.py     # 库存工具
│   ├── llm/                 # LLM客户端
│   │   ├── client.py        # 统一LLM客户端
│   │   ├── schemas.py       # 数据模型
│   │   └── providers/       # LLM提供商实现
│   ├── services/            # 服务模块
│   │   └── pharmacy_client.py # 后端HTTP客户端
│   ├── cli/                 # 命令行界面
│   │   ├── doctor_cli.py    # 医生CLI
│   │   └── interactive.py   # 交互式界面
│   └── tests/               # P1测试套件
│
├── Makefile                  # 项目构建工具
├── conftest.py              # pytest配置
└── docs/                    # 文档目录
```

## 📚 API概览

### 健康检查
- `GET /api/health` - 系统健康状态（包含ROS2连接状态）

### 药品管理
- `GET /api/drugs` - 获取所有药品（支持名称过滤）
- `GET /api/drugs/{id}` - 获取特定药品详情

### 订单处理
- `GET /api/orders` - 查看取药记录（最近50条）
- `POST /api/order` - 批量取药（库存扣减+ROS2任务发布）

### 审批流程
- `POST /api/approvals` - 创建医生审批单
- `GET /api/approvals/{id}` - 查询审批单详情
- `GET /api/approvals/pending` - 获取待审批列表
- `POST /api/approvals/{id}/approve` - 批准审批单
- `POST /api/approvals/{id}/reject` - 拒绝审批单

### ROS2任务消息格式
```json
{
  "task_id": 1,
  "type": "pickup",  // 或 "expiry_removal"
  "drug_id": 1,
  "name": "阿莫西林",
  "shelve_id": 1,
  "x": 1,
  "y": 1,
  "quantity": 2
}
```

## 🔧 开发工作流

### 日常开发
```bash
# 启动后端服务
make backend-start

# 设置P1环境变量
export PHARMACY_BASE_URL=http://localhost:8001

# 运行P1单元测试（mock后端）
cd P1 && pytest tests/

# 运行完整集成测试（需要后端运行）
make test-integration
```

### 环境配置
关键环境变量：
```bash
# P1医疗助手配置
LLM_PROVIDER=claude                    # LLM提供商：claude或openai
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic  # DeepSeek API地址
ANTHROPIC_AUTH_TOKEN=sk-your-api-key  # API密钥
PHARMACY_BASE_URL=http://localhost:8001 # 后端服务地址

# 后端配置
PORT=8001                             # 服务端口
EXPIRY_SWEEP_INTERVAL_SEC=3600        # 过期清扫间隔（秒）
```

### 调试工具
```bash
# 查看后端日志
cd backend && python main.py

# 启用调试日志
export LOG_LEVEL=DEBUG

# 直接查询数据库
sqlite3 backend/pharmacy.db "SELECT * FROM inventory;"
```

## 🧪 测试指南

### 当前测试状态
**待开发** - 完整的端到端测试套件正在规划中

### 现有测试能力
1. **P1单元测试** - 工具函数、LLM客户端、Agent核心逻辑测试
2. **后端API测试** - 基本端点功能验证
3. **集成测试** - P1与后端HTTP API通信测试

### 测试运行
```bash
# 运行P1单元测试
cd P1 && pytest tests/

# 运行后端测试
cd backend && pytest tests/

# 运行集成测试（需要后端服务运行）
export PHARMACY_BASE_URL=http://localhost:8001
cd P1 && RUN_INTEGRATION_TESTS=1 pytest tests/integration/
```

### 测试计划
- [ ] 端到端医疗咨询工作流测试
- [ ] ROS2任务发布与状态跟踪测试
- [ ] 并发用户场景压力测试
- [ ] 数据库迁移和兼容性测试

---

*最后更新：2026年4月15日*  
*项目状态：开发中 - 核心功能已实现*