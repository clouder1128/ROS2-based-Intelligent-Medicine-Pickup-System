# ROS2智能药品拣选系统 - Agent与后端集成

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-API-brightgreen)

集成的智能药品拣选系统，结合AI医疗助手与自动化药房后端，实现从医疗咨询到机器人取药的完整工作流。

## 核心特性

- **AI医疗咨询**：症状分析、药品推荐、剂量计算、多药联用
- **多LLM提供商**：支持 OpenAI、DeepSeek 等
- **药品数据库**：内置 116 种药品（12 大类，599 条适应症）
- **自动化药房**：药品管理、订单处理、审批流程、库存管理
- **ROS2 集成**：审批后自动派发取药任务到机器人
- **智能筛选**：基于症状的药品匹配与排序

## 快速开始

```bash
# 1. 创建并进入虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少设置 OPENAI_API_KEY

# 3. 一键启动（自动安装依赖、初始化数据库、启动前后端）
./quick_start.sh
```

启动后访问：
- **前端**：http://localhost:8080
- **后端**：http://localhost:8001

### 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 患者 | patient1 | 123456 |
| 医生 | doctor1 | 123456 |
| 管理员 | admin1 | 123456 |

## 项目结构

```
agent_with_backend/
├── agent/                    # AI 医疗助手
│   ├── engine/               # 引擎与工作流
│   ├── llm/                  # LLM 客户端
│   ├── subagents/            # 子代理（症状提取等）
│   └── tools/                # 工具系统
├── api/                      # Flask API 控制器
├── auth/                     # 认证与权限（JWT + RBAC）
├── common/                   # 通用模块（配置、缓存、工具）
├── database/                 # 数据库层（模型、脚本、种子数据）
├── ros_integration/          # ROS2 通信桥接
├── screening/                # 智能药品筛选
├── web/                      # 前端页面
├── main.py                   # 应用入口
└── quick_start.sh            # 一键启动脚本
```

## API 概览

- `GET /api/health` — 健康检查
- `GET /api/drugs` — 药品列表（支持 symptom/name/category 筛选）
- `GET /api/drugs/<id>` — 药品详情
- `POST /api/approvals` — 创建审批
- `GET /api/approvals/pending` — 待审批列表
- `POST /api/approvals/<id>/approve|reject` — 审批操作
- `POST /api/auth/login` — 用户登录
- `GET /api/ros/status` — ROS2 状态
- `POST /api/screening/query` — 智能筛选查询

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `openai` | LLM 提供商 |
| `OPENAI_API_KEY` | - | API 密钥 |
| `LLM_MODEL` | `deepseek-chat` | 模型名 |
| `HOST` | `0.0.0.0` | 服务地址 |
| `PORT` | `8001` | 后端端口 |
| `ENABLE_ROS2` | `true` | 启用 ROS2 集成 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
