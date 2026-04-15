# 智能药房后端系统

![Flask](https://img.shields.io/badge/Flask-API-brightgreen)
![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange)

智能药房后端服务，提供药品库存管理、订单处理、医生审批等REST API，集成ROS2实现自动化取药任务发布和过期药品清理。

## 📖 目录
- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API概览](#api概览)
- [ROS2集成](#ros2集成)
- [配置指南](#配置指南)
- [测试说明](#测试说明)

## 🧪 项目简介

智能药房后端是一个Flask REST API服务，为智能药品拣选系统提供核心业务逻辑支持。系统包含药品库存管理、订单处理、医生审批流程，并与ROS2机器人控制系统集成，实现自动化取药任务发布。

**主要功能**：
- 药品库存管理和有效期跟踪
- 取药订单处理和库存扣减
- 医生电子审批工作流
- ROS2任务发布和状态监控
- 过期药品自动清理

## ⚡ 核心特性

### 库存管理
- **实时库存跟踪**：药品数量、有效期、货架位置管理
- **有效期管理**：自动过期检查和清理
- **库存扣减**：事务安全的库存更新机制

### 订单处理
- **批量取药**：支持多药品同时取药
- **订单记录**：完整的取药历史跟踪
- **状态管理**：订单状态（pending、processing、completed）跟踪

### ROS2集成
- **任务发布**：自动化发布取药任务到ROS2话题
- **状态订阅**：监控机器人执行状态
- **错误处理**：任务失败时的优雅降级

### 审批流程
- **电子审批**：完整的医生审批工作流
- **状态跟踪**：审批单状态（pending、approved、rejected）管理
- **历史记录**：审批操作审计日志

## 🏗️ 系统架构

```
┌─────────────────┐     HTTP API     ┌─────────────────┐
│   前端/P1系统    │◄────────────────►│   智能药房后端   │
│                 │   (8001端口)     │                 │
│  • Web界面      │                  │  • Flask API    │
│  • P1医疗助手   │                  │  • SQLite DB    │
│  • 其他客户端   │                  │  • 业务逻辑     │
└─────────────────┘                  └────────┬────────┘
                                              │
                                              │ ROS2话题
                                              ▼
                                       ┌──────────────┐
                                       │  ROS2节点    │
                                       │  • 任务执行  │
                                       │  • 状态反馈  │
                                       └──────────────┘
```

**核心组件**：
1. **Flask API层** - REST API端点处理HTTP请求
2. **业务逻辑层** - 库存管理、订单处理、审批流程
3. **数据访问层** - SQLite数据库操作和模型定义
4. **ROS2集成层** - 任务发布、状态订阅、错误处理
5. **定时任务层** - 过期药品自动清理

## 🚀 快速开始

### 环境要求
- Python 3.8+
- ROS2 Jazzy（可选，仅ROS2集成需要）
- SQLite 3（默认包含）

### 安装步骤
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

### 服务验证
```bash
# 健康检查
curl http://localhost:8001/api/health

# 查看药品列表
curl http://localhost:8001/api/drugs

# 查看待审批列表
curl http://localhost:8001/api/approvals/pending
```

### 启动选项
```bash
# 指定端口
PORT=8080 python main.py

# 启用调试模式
FLASK_DEBUG=1 python main.py

# 缩短过期清扫间隔（测试用）
EXPIRY_SWEEP_INTERVAL_SEC=60 python main.py
```

## 📁 项目结构

```
backend/
├── main.py                    # Flask主应用入口
│
├── controllers/              # API控制器
│   ├── health_controller.py  # 健康检查API
│   ├── drug_controller.py    # 药品管理API
│   ├── order_controller.py   # 订单处理API
│   └── approval_controller.py # 审批流程API
│
├── models/                   # 数据模型
│   ├── drug.py              # 药品模型
│   ├── order.py             # 订单模型
│   └── approval.py          # 审批模型
│
├── ros_integration/         # ROS2集成模块
│   ├── task_publisher.py    # 任务发布器
│   ├── state_subscriber.py  # 状态订阅器
│   ├── message_adapter.py   # 消息适配器
│   ├── health_monitor.py    # 健康监控
│   ├── error_handler.py     # 错误处理器
│   └── node_manager.py      # 节点管理器
│
├── utils/                   # 工具函数
│   ├── database.py          # 数据库操作
│   ├── logger.py            # 日志配置
│   ├── ros2_bridge.py       # ROS2桥接工具
│   └── drug_helpers.py      # 药品辅助函数
│
├── config/                  # 配置管理
│   └── settings.py          # 应用配置
│
├── tests/                   # 测试套件
│   ├── test_drug_api.py     # 药品API测试
│   ├── test_approval_api.py # 审批API测试
│   └── test_ros_integration.py # ROS2集成测试
│
├── pharmacy.db             # SQLite数据库文件
└── init_db.py             # 数据库初始化脚本
```

## 📚 API概览

### 健康检查
- `GET /api/health` - 系统健康状态（含ROS2连接状态）

### 药品管理
- `GET /api/drugs` - 获取所有药品（支持`?name=药品名`过滤）
- `GET /api/drugs/{id}` - 获取特定药品详情
- `GET /api/orders` - 查看取药记录（最近50条）

### 订单处理
- `POST /api/order` - 批量取药（库存扣减+ROS2任务发布）
- `POST /api/pickup` - 单条取药（兼容旧接口）

### 审批流程
- `POST /api/approvals` - 创建医生审批单
- `GET /api/approvals/{id}` - 查询审批单详情
- `GET /api/approvals/pending` - 获取待审批列表
- `POST /api/approvals/{id}/approve` - 批准审批单
- `POST /api/approvals/{id}/reject` - 拒绝审批单

### 请求/响应示例

**批量取药请求**：
```json
[
  { "id": 1, "num": 2 },
  { "id": 2, "num": 1 }
]
```

**成功响应**：
```json
{
  "ok": true,
  "task_ids": [1, 2],
  "message": "已下发 2 个取药任务，库存已扣减"
}
```

## 🤖 ROS2集成

### 任务发布
后端向ROS2话题`/task_request`发布JSON格式任务消息：

**用户取药任务**：
```json
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
```

**过期清理任务**：
```json
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

### 状态订阅
后端订阅ROS2话题获取任务执行状态，支持：
- 任务开始通知
- 任务完成确认
- 任务失败处理

### 错误处理
- ROS2节点未连接时的优雅降级
- 任务发布失败的重试机制
- 网络异常的自动恢复

## 🔧 配置指南

### 环境变量
```bash
# 服务配置
PORT=8001                            # 服务端口（默认8001）
FLASK_DEBUG=0                        # 调试模式（0=关闭，1=开启）

# 数据库配置
DATABASE_URL=sqlite:///pharmacy.db   # 数据库连接字符串

# ROS2配置
ROS2_ENABLED=1                       # ROS2集成开关（0=禁用，1=启用）
ROS2_NODE_NAME=pharmacy_backend      # ROS2节点名称

# 定时任务配置
EXPIRY_SWEEP_INTERVAL_SEC=3600       # 过期清扫间隔（秒，默认1小时）
```

### 数据库管理
```bash
# 初始化数据库（重置示例数据）
python init_db.py

# 重置数据库
rm pharmacy.db && python init_db.py

# 直接查询数据库
sqlite3 pharmacy.db "SELECT * FROM inventory;"
sqlite3 pharmacy.db "SELECT * FROM order_log;"
sqlite3 pharmacy.db "SELECT * FROM approvals;"
```

### 数据库表结构
| 表名 | 说明 |
|------|------|
| `inventory` | 药品库存表（名称、数量、有效期、货架位置） |
| `order_log` | 取药记录表（任务ID、药品ID、数量、状态） |
| `approvals` | 审批单表（患者、建议、状态、审批人） |
| `app_meta` | 应用元数据表（过期清扫基准日等） |
| `audit_logs` | 审计日志表（操作记录） |

## 🧪 测试说明

### 测试运行
```bash
# 进入后端目录
cd backend

# 运行所有测试
pytest tests/

# 运行特定测试模块
pytest tests/test_drug_api.py -v          # 药品API测试
pytest tests/test_approval_api.py -v      # 审批API测试
pytest tests/test_ros_integration.py -v   # ROS2集成测试

# 运行集成测试
pytest tests/test_e2e_workflow.py -v      # 端到端工作流测试
```

### 测试策略
- **单元测试**：API端点功能验证
- **集成测试**：模块间交互测试
- **端到端测试**：完整工作流测试
- **ROS2集成测试**：ROS2功能测试（需ROS2环境）

### 测试覆盖率
```bash
# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 查看覆盖率摘要
pytest tests/ --cov=. --cov-report=term-missing
```

## 🔄 开发工作流

### 日常开发
```bash
# 启动开发服务器
python main.py

# 启用调试日志
export LOG_LEVEL=DEBUG
python main.py

# 运行测试确保功能正常
pytest tests/
```

### API调试
```bash
# 使用curl测试API
curl http://localhost:8001/api/health
curl http://localhost:8001/api/drugs
curl -X POST http://localhost:8001/api/order -d '[{"id":1,"num":2}]' -H "Content-Type: application/json"

# 使用HTTP客户端工具
# 推荐使用Postman、curl或httpie
```

### 故障排除

**常见问题**：
1. **端口冲突**：确保端口8001未被占用
2. **数据库锁定**：检查是否有其他进程使用pharmacy.db
3. **ROS2连接失败**：确认ROS2环境已正确配置
4. **依赖问题**：运行`pip install -r requirements.txt`

**日志查看**：
```bash
# 查看应用日志
tail -f backend.log

# 启用详细日志
export LOG_LEVEL=DEBUG
python main.py 2>&1 | tee debug.log
```

---

*最后更新：2026年4月15日*  
*项目状态：开发中 - 核心功能已实现，API稳定*