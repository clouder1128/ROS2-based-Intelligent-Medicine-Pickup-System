# ROS2-based Intelligent Medicine Pickup System

![ROS2 Jazzy](https://img.shields.io/badge/ROS2-Jazzy-blue)
![Ubuntu 24.04](https://img.shields.io/badge/Ubuntu-24.04-orange)
![Gazebo Harmonic](https://img.shields.io/badge/Gazebo-Harmonic-green)
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-API-brightgreen)

A comprehensive intelligent medicine pickup system combining ROS2-based robotic simulation with AI medical assistant for intelligent pharmacy operations.

## 📖 目录

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [开发工作流](#开发工作流)
- [API文档](#api文档)
- [测试](#测试)

## 🧪 项目简介

本项目是一个集成的智能药品拣选系统，包含两个主要组件：

1. **智能药房后端（Flask服务）** - 提供药品库存管理、订单处理、医生审批等REST API，支持ROS2任务发布和定时过期清扫
2. **P1医疗助手系统（AI Agent）** - 基于LLM的医疗用药助手，提供症状咨询、药品查询、审批提交等智能功能

**核心特性**:
- **智能药房管理**：药品库存、有效期管理、货架定位
- **ROS2集成**：自动化取药任务发布到仿真系统
- **AI医疗助手**：症状分析、药品推荐、剂量计算
- **医生审批流程**：完整的电子审批工作流
- **定时任务**：自动过期药品清扫和库存管理

## 🏗️ 系统架构

### 整体架构
```
┌─────────────────┐     HTTP API     ┌─────────────────┐
│   P1 Medical    │◄────────────────►│   Smart Pharmacy │
│    Assistant    │   (端口8001)     │    Backend      │
│                 │                  │                 │
│  • LLM Agent    │                  │  • Flask API    │
│  • Medical Tools│                  │  • SQLite DB    │
│  • Workflows    │                  │  • ROS2 Bridge  │
│  • Memory       │                  │  • Timed Tasks  │
└─────────────────┘                  └────────┬────────┘
         │                                    │ ROS2
         │                                    │ /task_request
         └────────────────────────────────────┘
                     (Future: Simulation)
```

### 技术栈
- **后端服务**：Flask + SQLite + ROS2 (rclpy)
- **AI助手**：Python + Claude/OpenAI/DeepSeek API + 异步工具调用
- **通信协议**：HTTP REST API + ROS2话题
- **数据库**：SQLite（pharmacy.db）用于药品库存和审批记录

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd agent

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装P1依赖
cd ../P1
pip install -r requirements.txt
```

### 2. 启动集成环境
```bash
# 一键启动（推荐）
make quick-start

# 或者分步启动
# 终端1: 启动后端服务
make backend-start

# 终端2: 启动P1 CLI
cd P1
export PHARMACY_BASE_URL=http://localhost:8001
python cli.py
```

### 3. 验证安装
```bash
# 检查后端健康
curl http://localhost:8001/api/health

# 检查P1连接
cd P1
python -c "import drug_db; print(drug_db.health_check())"
```

## 📁 项目结构

```
agent/
├── backend/                    # 智能药房后端服务
│   ├── app.py                 # Flask主应用（API端点）
│   ├── approval.py            # 审批管理模块
│   ├── init_db.py             # 数据库初始化
│   ├── requirements.txt       # Python依赖
│   ├── pharmacy.db           # SQLite数据库文件
│   └── tests/                 # 后端测试
│       ├── test_approval_api.py
│       └── test_drug_api.py
│
├── P1/                        # AI医疗助手系统
│   ├── cli.py                 # 命令行界面
│   ├── drug_db.py             # 药品数据库接口（HTTP客户端）
│   ├── example_usage.py       # 使用示例脚本
│   ├── example_http_client.py # HTTP客户端示例
│   ├── interactive.py         # 简单交互式命令行界面
│   ├── run_tests.py           # 测试运行器
│   ├── config.py              # 配置管理
│   ├── exceptions.py          # 异常定义
│   ├── core/                  # 核心模块
│   │   ├── agent.py           # MedicalAgent主类
│   │   └── workflows.py       # 工作流管理器
│   ├── llm/                   # LLM客户端和提供商
│   │   ├── client.py          # 统一LLM客户端
│   │   ├── schemas.py         # 数据模型
│   │   └── providers/         # LLM提供商实现
│   ├── tools/                 # 工具系统
│   │   ├── base.py            # 工具基类
│   │   ├── executor.py        # 工具执行器
│   │   ├── registry.py        # 工具注册表
│   │   ├── inventory.py       # 库存管理工具
│   │   ├── medical.py         # 医疗工具
│   │   └── report_generator.py # 报告生成工具
│   ├── utils/                 # 工具函数
│   │   ├── http_client.py     # HTTP客户端工具
│   │   ├── json_tools.py      # JSON处理工具
│   │   ├── text_utils.py      # 文本处理工具
│   │   ├── validation.py      # 验证工具
│   │   └── retry.py           # 重试机制
│   ├── memory/                # 消息和记忆管理
│   │   ├── manager.py         # 消息管理器
│   │   └── compressor.py      # 消息压缩器
│   ├── session/               # 会话管理
│   │   └── manager.py         # 会话管理器
│   └── tests/                 # 测试套件
│       ├── conftest.py        # pytest配置
│       ├── integration/       # 集成测试
│       ├── test_core.py       # Agent核心测试
│       ├── test_drug_db_simple.py    # 药品数据库简单测试
│       ├── test_drug_db_integration.py # 药品数据库集成测试
│       ├── test_http_client.py        # HTTP客户端测试
│       ├── test_inventory_integration.py # 库存集成测试
│       ├── test_llm.py        # LLM测试
│       ├── test_medical_integration.py # 医疗集成测试
│       ├── test_memory.py     # 内存测试
│       ├── test_session.py    # 会话管理测试
│       ├── test_tools.py      # 工具测试
│       └── test_utils.py      # 工具函数测试
│
├── scripts/                   # 实用脚本
│   ├── quick-start.sh         # 一键启动脚本
│   └── test-full-integration.py # 完整集成测试
│
├── docs/                      # 文档
│   ├── integration-guide.md   # 集成指南
│   ├── troubleshooting.md     # 故障排除
│   ├── api-reference.md       # API参考文档
│   └── superpowers/           # 开发规划文档
│
├── tests/                     # 根目录测试文件
│   └── test_backend_config.py # 后端配置测试
├── test/                     # ROS2仿真测试目录
│   ├── readme.md             # 仿真测试说明
│   ├── test_world.sdf        # Gazebo仿真世界文件
│   ├── models/               # 机器人模型
│   └── line_follower/        # 巡线算法ROS2包
│
├── Makefile                   # 项目构建工具
├── 团队通知.md                # 团队开发通知
├── AI 开药助手 —— 团队项目说明文档 ver 3.0.md # 团队项目说明文档
├── API密钥安全指南.md         # API密钥安全指南
├── backend-to-p1-integration-analysis.md # 后端-P1集成分析
└── README.md                  # 本文件
```

## 🔧 开发工作流

### 日常开发
```bash
# 启动后端服务（端口8001）
make backend-start

# 设置环境变量
export PHARMACY_BASE_URL=http://localhost:8001

# 运行P1测试
cd P1 && pytest tests/

# 运行集成测试
make test-integration
```

### 测试策略
- **单元测试**：P1工具函数和backend API端点
- **集成测试**：P1 ↔ Backend HTTP API调用
- **完整测试**：端到端医疗咨询流程测试

### 调试工具
```bash
# 查看后端日志
cd backend && python app.py

# 启用调试日志
export LOG_LEVEL=DEBUG
```

## 📚 API文档

### 后端API端点
- `GET /api/health` - 健康检查（含ROS2状态）
- `GET /api/drugs` - 获取所有药品（支持名称过滤）
- `GET /api/drugs/{id}` - 获取特定药品
- `GET /api/orders` - 查看取药记录（最近50条）
- `POST /api/order` - 批量取药（库存扣减+ROS2任务）
- `POST /api/pickup` - 单条取药（兼容旧接口）
- `POST /api/approvals` - 创建医生审批单
- `GET /api/approvals/{id}` - 查询审批单
- `GET /api/approvals/pending` - 获取待审批列表
- `POST /api/approvals/{id}/approve` - 批准审批单
- `POST /api/approvals/{id}/reject` - 拒绝审批单

详细API文档见 [docs/integration-guide.md](docs/integration-guide.md)

## 🧪 测试

### 运行测试
```bash
# 运行P1单元测试（mock后端）
make test

# 运行完整集成测试（需要后端运行）
make test-integration

# 运行特定测试模块
cd P1 && pytest tests/test_drug_db_simple.py -v
```

### 测试环境配置
```bash
# 启用集成测试
export RUN_INTEGRATION_TESTS=1

# 设置测试数据库
cd backend && python init_db.py
```

## 🔧 维护与故障排除

### 常见问题
1. **端口冲突**：确保端口8001未被占用
2. **数据库锁定**：检查是否有其他进程使用pharmacy.db
3. **连接失败**：验证`PHARMACY_BASE_URL`环境变量
4. **依赖问题**：运行`pip install -r requirements.txt`

详细故障排除见 [docs/troubleshooting.md](docs/troubleshooting.md)

### 数据库管理
```bash
# 初始化数据库
cd backend && python init_db.py

# 重置数据库
cd backend && rm pharmacy.db && python init_db.py

# 直接查询数据库
sqlite3 backend/pharmacy.db "SELECT * FROM inventory;"
```

## 🤝 贡献指南

1. **开发流程**：参考[团队通知.md](团队通知.md)中的角色分工
2. **代码规范**：遵循现有代码结构和命名约定
3. **测试要求**：新功能需包含单元测试和集成测试
4. **文档更新**：代码变更需同步更新相关文档

## 📄 许可证

本项目仅供学习研究使用。

## 📞 联系方式

- **项目仓库**：https://github.com/clouder1128/ROS2-based-Intelligent-Medicine-Pickup-System
- **团队沟通**：参考团队内部沟通渠道

---

*最后更新：2026年4月7日*  
*项目状态：开发中 - 集成测试通过*