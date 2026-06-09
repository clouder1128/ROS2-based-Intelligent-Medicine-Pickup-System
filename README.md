# AI 药房问诊取药系统

AI 药房问诊取药系统，集成 AI 医疗咨询、自动化药房后端与 ROS2 机器人控制，实现从问诊到取药的完整工作流。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│  用户 (Web界面)                                                  │
│  http://localhost:8080                                            │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│  Ubuntu 24.04 (核心系统)                                         │
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │  AI 医疗助手     │    │  药房后端        │    │ ROS2 工作空间│  │
│  │  (agent/)       │◄──►│  Flask API       │◄──►│ ros_workspace│  │
│  │  LLM 驱动       │    │  药品/订单/审批   │    │ 机器人控制   │  │
│  └─────────────────┘    └─────────────────┘    └──────┬──────┘  │
│                                                        │        │
└────────────────────────────────────────────────────────┼────────┘
                                                         │ ROS2 TCP
┌────────────────────────────────────────────────────────┼────────┐
│  Windows (仿真)                                        │        │
│  ┌─────────────────┐                                   │        │
│  │ Unity 3D 仿真    │◄──────────────────────────────────┘        │
│  │ 药房场景/机器人   │   ros_tcp_endpoint                         │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

| 目录 / 文件 | 说明 |
|---|---|
| [setup.sh](setup.sh) | **一键安装脚本**（首次运行前执行一次） |
| [agent_with_backend/](agent_with_backend/) | 后端主程序（Flask API、AI Agent、前端页面） |
| [agent_with_backend/quick_start.sh](agent_with_backend/quick_start.sh) | **一键启动脚本**（每次运行系统用） |
| [docs/](docs/) | 项目文档 |
| [ros_workspace/](ros_workspace/) | ROS2 工作空间（机器人通信） |
| [unity_simulation/](unity_simulation/) | Unity 3D 仿真场景 |
| [tests/](tests/) | 测试用例 |

## 运行环境

| 组件 | 操作系统 | 依赖 |
|------|---------|------|
| **核心系统** | Ubuntu 24.04 | Python 3.12, ROS2 Humble|
| **Unity 仿真** | Windows 10/11 | Unity 2022.3+ |
| **Web 前端** | （浏览器访问） | 无额外依赖 |


## 快速启动

### 一键安装（首次运行）

项目根目录提供了 [setup.sh](setup.sh) 脚本，自动完成系统依赖安装、ROS2 构建、Python 虚拟环境创建、数据库初始化等全部环境配置。

```bash
# 完整安装（含 ROS2/Unity 联动）
./setup.sh

# 如果无需 Unity 仿真，跳过 ROS2 相关步骤
./setup.sh --no-ros
```

> 脚本执行过程中会自动提示配置 `.env` 文件。若未自动提示，请手动执行：
>
> ```bash
> cp agent_with_backend/.env.example agent_with_backend/.env
> # 编辑 .env，至少设置 OPENAI_API_KEY
> ```

### 日常启动

环境配置完成后，每次启动系统只需：

```bash
cd agent_with_backend
./quick_start.sh
```

`quick_start.sh` 启动后将自动：
- 启动后端 Flask 服务（端口 **8001**）
- 启动前端静态文件服务（端口 **8080**）
- 启动 ROS2 TCP Endpoint（端口 **10000**，用于 Unity 通信）

**访问地址**：
- 前端页面：http://localhost:8080
- 后端 API：http://localhost:8001/api/health

**演示账号**：
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin1 | 123456 |
| 医生 | doctor1 | 123456 |
| 患者 | patient1 | 123456 |

### 手动分步安装（可选）

如果希望了解每一步的具体作用，或需要自定义安装过程，可参考以下分步说明。

<details>
<summary>展开查看分步说明</summary>

#### 1. 安装 ROS2

> 如果无需 Unity 仿真联动，可跳过此步。

```bash
# Ubuntu 24.04 安装 ROS2 Jazzy
sudo apt update && sudo apt upgrade -y
sudo apt install ros-jazzy-ros-base python3-colcon-common-extensions -y

# 如果使用 Ubuntu 22.04，安装 ROS2 Humble
# sudo apt install ros-humble-ros-base python3-colcon-common-extensions -y

# 配置环境变量（建议添加到 ~/.bashrc）
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

#### 2. 安装 Python 依赖

```bash
sudo apt install python3-pip python3-venv -y
```

#### 3. 构建 ROS2 工作空间

> 如果无需 Unity 仿真联动，可跳过此步。

```bash
cd ros_workspace
colcon build --packages-select ros_tcp_endpoint task_msgs --symlink-install
source install/setup.bash
cd ..
```

> **提示**：`ros_tcp_endpoint` 是 ROS2 与 Unity 通信的桥接包，`task_msgs` 是自定义消息类型（任务派发、药柜状态等）。

#### 4. 配置 Python 虚拟环境

```bash
cd agent_with_backend
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cd ..
```

#### 5. 初始化数据库

```bash
cd agent_with_backend
source venv/bin/activate
python -m database.scripts.init_db
python -m database.scripts.seed_drugs
python -m database.scripts.seed_users
cd ..
```

> 数据库表结构在 `main.py` 启动时也会自动创建，但药品种子数据和演示用户（admin1/123456 等）仅在手动执行 seed 脚本时填充。

#### 6. 配置环境变量

```bash
cp agent_with_backend/.env.example agent_with_backend/.env
# 编辑 .env，至少设置 OPENAI_API_KEY
```

</details>

## Unity 仿真配置（Windows）

> 如果无需 Unity 仿真联动，可跳过本节。

### 1. 环境要求

- Windows 10/11
- Unity 2022.3 或更高版本
- Ubuntu 和 Windows 需要在**同一局域网**内

### 2. 启动仿真

**方法一：直接运行（推荐）**

进入 `unity_simulation/` 目录，找到打包好的可执行文件：

```
unity_simulation/
├── RosCar/
│   └── ROSPackage.exe      ← 双击运行
└── ROSPackage/
    └── Assets/             ← Unity 项目源码
```

双击 `ROSPackage.exe` 即可启动仿真场景。

**方法二：使用 Unity Editor 打开**

1. 打开 Unity Hub
2. 点击 "Open" → 选择 `unity_simulation/ROSPackage/` 目录
3. 等待项目加载完成
4. 在 Unity Editor 中点击播放按钮运行

### 3. 配置 ROS2 连接

在 Unity 中设置 ROS2 连接参数（对应 Ubuntu 主机 IP）：

| 参数 | 值 |
|------|-----|
| ROS IP | Ubuntu 主机的局域网 IP 地址 |
| ROS TCP Port | 10000 |

> **提示**：在 Ubuntu 上执行 `ip addr` 查看本机 IP，确保与 Windows 处于同一网段。

## 技术栈

- **后端**：Python 3.12, Flask, SQLite
- **AI**：OpenAI / DeepSeek API, Function Calling
- **机器人**：ROS2 Humble, ros_tcp_endpoint
- **仿真**：Unity 3D
- **前端**：原生 HTML/CSS/JS

## 文档

详见 [docs/](docs/) 目录下的详细文档。
