# AI 药房问诊取药系统

AI 药房问诊取药系统，集成 AI 医疗咨询、自动化药房后端与 ROS2 机器人控制，实现从问诊到取药的完整工作流。

## 系统架构

```
用户 (Web界面)
    │
    ├── AI 医疗助手 (agent/)        ── LLM 驱动，症状分析、药品推荐
    ├── 药房后端 (agent_with_backend/) ── Flask API，药品/订单/审批管理
    ├── ROS2 集成 (ros_workspace/)    ── 机器人任务派发与控制
    └── Unity 仿真 (unity_simulation/) ── 3D 药房场景仿真
```

## 目录结构

| 目录 | 说明 |
|------|------|
| [agent_with_backend/](agent_with_backend/) | 后端主程序（Flask API、AI Agent、前端页面） |
| [docs/](docs/) | 项目文档 |
| [ros_workspace/](ros_workspace/) | ROS2 工作空间（机器人通信） |
| [unity_simulation/](unity_simulation/) | Unity 3D 仿真场景 |
| [tests/](tests/) | 测试用例 |

## 快速启动

```bash
cd agent_with_backend

# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，设置 OPENAI_API_KEY

# 3. 一键启动
./quick_start.sh
```

启动后访问 **http://localhost:8080**（演示账号：admin1 / 123456）。

## 技术栈

- **后端**：Python 3.12, Flask, SQLite
- **AI**：OpenAI / DeepSeek API, Function Calling
- **机器人**：ROS2 Humble, ros_tcp_endpoint
- **仿真**：Unity 3D
- **前端**：原生 HTML/CSS/JS

## 文档

详见 [docs/](docs/) 目录下的详细文档。
