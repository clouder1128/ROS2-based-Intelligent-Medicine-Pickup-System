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

## 运行环境

| 组件 | 操作系统 | 依赖 |
|------|---------|------|
| **核心系统** | Ubuntu 24.04 | Python 3.12, ROS2 Humble/Jazzy |
| **Unity 仿真** | Windows 10/11 | Unity 2022.3+ |
| **Web 前端** | （浏览器访问） | 无额外依赖 |

---

# 完整使用步骤

## 一、Ubuntu 环境准备

### 1. 安装 ROS2

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

### 2. 安装 Python 依赖

```bash
# 确保 Python 3.12 可用
python3 --version

# 安装 pip
sudo apt install python3-pip python3-venv -y
```

### 3. 构建 ROS2 工作空间

> 如果无需 Unity 仿真联动，可跳过此步。

```bash
cd ros_workspace
colcon build --packages-select ros_tcp_endpoint task_msgs --symlink-install
source install/setup.bash
cd ..
```

> **提示**：`ros_tcp_endpoint` 是 ROS2 与 Unity 通信的桥接包，`task_msgs` 是自定义消息类型（任务派发、药柜状态等）。

---

## 二、后端配置与启动

### 1. 创建 Python 虚拟环境（已包含在项目内）

```bash
cd agent_with_backend

# 如果 venv 目录不存在，则重新创建
if [ ! -d "venv" ]; then
    python3 -m venv --system-site-packages venv
fi

# 激活虚拟环境
source venv/bin/activate
```

### 2. 安装 Python 依赖

```bash
# 升级 pip
pip install --upgrade pip setuptools wheel

# 安装依赖（如果在全新环境中）
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 从模板创建 .env 文件
cp .env.example .env
```

编辑 `.env` 文件，至少需要设置以下项：

| 变量 | 必填 | 说明 |
|------|------|------|
| `OPENAI_API_KEY` | ✅ | DeepSeek / OpenAI API 密钥 |
| `LLM_PROVIDER` | 否 | 默认 `openai`（兼容 DeepSeek） |
| `LLM_MODEL` | 否 | 默认 `deepseek-chat` |
| `OPENAI_BASE_URL` | 否 | 默认 `https://api.deepseek.com` |

> **如果没有 API Key**：系统仍可启动和使用药品管理、订单等基本功能，仅 AI 问诊功能不可用。

### 4. 初始化数据库与种子数据

```bash
# 确保在 agent_with_backend 目录且 venv 已激活
python -m database.scripts.init_db
python -m database.scripts.seed_drugs
python -m database.scripts.seed_users
```

### 5. 一键启动

```bash
# 确保在 agent_with_backend 目录
./quick_start.sh
```

启动后将自动：
- 启动后端 Flask 服务（端口 8001）
- 启动前端静态文件服务（端口 8080）
- 启动 ROS2 TCP Endpoint（端口 10000，用于 Unity 通信）

**访问地址**：
- 前端页面：http://localhost:8080
- 后端 API：http://localhost:8001/api/health

---

## 三、Unity 仿真配置（Windows）

### 1. 环境要求

- Windows 10/11
- Unity 2022.3 或更高版本

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

> **提示**：Ubuntu 和 Windows 需要在同一局域网内。在 Ubuntu 上执行 `ip addr` 查看本机 IP。

### 4. Unity 仿真功能

| 功能 | 说明 |
|------|------|
| AGV 小车展示 | 显示取药机器人在药房场景中的移动 |
| 药柜状态 | 展示药柜库存和药品位置 |
| 任务执行 | 接收 ROS2 任务消息并驱动仿真动画 |
| 实时状态回传 | 将小车位置、任务状态回传给后端 |

---

## 四、系统使用指南

### 演示账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin1 | 123456 | 管理后台、药品管理、查看所有数据 |
| 医生 | doctor1 | 123456 | 审批处方、查看药品 |
| 医生 | doctor2 | 123456 | 同上 |
| 患者 | patient1 | 123456 | 问诊、查看药品 |
| 患者 | patient2 | 123456 | 同上 |

### 完整工作流程

```
1. 患者登录
   → 访问 http://localhost:8080
   → 选择「患者」角色 → 输入 patient1 / 123456 登录

2. 智能问诊
   → 在患者页面描述症状（如"头痛发热"）
   → AI Agent 分析症状 → 推荐药品 → 生成用药建议

3. 医生审批
   → 使用 doctor1 账号登录
   → 查看待审批处方 → 批准/拒绝
   → 审批通过后自动触发取药

4. 取药执行（需 Unity 仿真联动）
   → ROS2 接收取药任务 → 派发 AGV 小车 → 到达药柜取药
   → Unity 仿真展示完整过程

5. 订单追踪
   → 管理员可在后台查看所有订单状态
```

### 功能页面

| 页面 | 路径 | 角色 |
|------|------|------|
| 登录页 | `/` | 所有 |
| 患者问诊 | `/patient.html` | 患者 |
| 医生审批 | `/doctor.html` | 医生 |
| 管理后台 | `/admin.html` | 管理员 |
| 药品管理 | `/admin_drugs.html` | 管理员 |
| 订单管理 | `/admin_orders.html` | 管理员 |
| ROS2 监控 | `/ros_monitor.html` | 管理员 |
| 注册页 | `/register.html` | 所有 |

---

## 五、项目结构

```
项目根目录/
├── agent_with_backend/         # 核心后端 + 前端 + AI Agent
│   ├── agent/                  # AI 医疗助手（LLM Agent）
│   ├── api/                    # Flask API 控制器
│   ├── auth/                   # 认证权限（JWT + RBAC）
│   ├── common/                 # 通用模块（配置、缓存、工具）
│   ├── database/               # 数据库层（模型、脚本、种子数据）
│   ├── ros_integration/        # ROS2 通信桥接
│   ├── screening/              # 智能药品筛选引擎
│   ├── web/                    # 前端页面（HTML/CSS/JS）
│   ├── venv/                   # Python 虚拟环境
│   ├── main.py                 # 后端入口
│   ├── quick_start.sh          # 一键启动脚本
│   └── requirements.txt        # Python 依赖
├── ros_workspace/              # ROS2 工作空间
│   └── src/
│       ├── ROS-TCP-Endpoint/   # ROS2-Unity 通信桥接
│       └── task_msgs/          # 自定义消息类型
├── unity_simulation/           # Unity 3D 仿真
│   ├── RosCar/                 # 打包好的可执行文件
│   └── ROSPackage/             # Unity 项目源码
├── docs/                       # 项目文档
│   ├── 测试分析报告.pdf
│   ├── 测试计划.pdf
│   └── 开发文件/
└── tests/                      # 测试用例
```

---

## 六、常见问题

### Q: 没有 API Key 能运行吗？
可以。系统的基本功能（药品管理、订单、登录、审批）不依赖 LLM。仅 AI 问诊功能不可用。

### Q: 没有 ROS2 环境能运行吗？
可以。后端会自动检测 ROS2 环境，若不可用则跳过 ROS2 相关功能，不影响 Web 端使用。

### Q: Unity 仿真无法连接 ROS2？
1. 检查 Ubuntu 和 Windows 是否在同一局域网
2. 检查 Ubuntu 防火墙：`sudo ufw allow 10000`
3. 在 Unity 中确认 ROS IP 地址是否正确

### Q: 如何重新构建 ROS2 工作空间？
```bash
cd ros_workspace
rm -rf build/ install/ log/
colcon build --packages-select ros_tcp_endpoint task_msgs --symlink-install
source install/setup.bash
```

### Q: 数据库损坏如何重置？
```bash
cd agent_with_backend
rm -f pharmacy.db
source venv/bin/activate
python -m database.scripts.init_db
python -m database.scripts.seed_drugs
python -m database.scripts.seed_users
```

---

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.12 + Flask | 后端 REST API |
| SQLite | 数据库 |
| OpenAI / DeepSeek API | AI 医疗咨询（LLM Function Calling） |
| ROS2 Humble/Jazzy | 机器人任务派发控制 |
| Unity 2022.3 | 3D 药房仿真场景 |
| ros_tcp_endpoint | ROS2 ↔ Unity 通信桥接 |
| HTML/CSS/JS | 前端页面（原生） |
| JWT + RBAC | 认证与权限控制 |
