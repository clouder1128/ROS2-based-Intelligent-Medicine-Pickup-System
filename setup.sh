#!/usr/bin/env bash
# setup.sh - 一键安装环境（首次运行前执行一次）
#
# 整合以下 README 步骤：
#   1. 安装 ROS2（可选）
#   2. 安装 Python 依赖
#   3. 构建 ROS2 工作空间（可选）
#   4. 创建虚拟环境 + 安装 Python 包
#   5. 初始化数据库 + 种子数据
#   6. 提示配置 .env
#
# 用法:
#   ./setup.sh             # 完整安装（含 ROS2/Unity 联动）
#   ./setup.sh --no-ros    # 跳过 ROS2 相关步骤（纯后端）
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/agent_with_backend"
ROS_WS_DIR="$ROOT_DIR/ros_workspace"
WITH_ROS=true

for arg in "$@"; do
    [ "$arg" = "--no-ros" ] && WITH_ROS=false
done

echo "============================================"
echo "  智能药品管理系统 - 一键环境配置"
echo "============================================"
echo ""

# ──────────────────────────────────────────────
# 1. 系统依赖
# ──────────────────────────────────────────────
echo "[1/6] 安装系统依赖..."
sudo apt update && sudo apt upgrade -y

if [ "$WITH_ROS" = true ]; then
    sudo apt install -y \
        ros-jazzy-ros-base \
        python3-colcon-common-extensions \
        python3-pip python3-venv
    # 配置 ROS2 环境变量（仅首次追加）
    grep -qxF "source /opt/ros/jazzy/setup.bash" ~/.bashrc 2>/dev/null \
        || echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
    # 当前会话生效
    if [ -f /opt/ros/jazzy/setup.bash ]; then
        source /opt/ros/jazzy/setup.bash
    fi
else
    sudo apt install -y python3-pip python3-venv
fi

# ──────────────────────────────────────────────
# 2. Python 版本确认
# ──────────────────────────────────────────────
echo "[2/6] 验证 Python 环境..."
python3 --version
pip3 --version

# ──────────────────────────────────────────────
# 3. 构建 ROS2 工作空间（可选）
# ──────────────────────────────────────────────
if [ "$WITH_ROS" = true ] && [ -d "$ROS_WS_DIR" ]; then
    echo "[3/6] 构建 ROS2 工作空间..."
    cd "$ROS_WS_DIR"
    colcon build --packages-select ros_tcp_endpoint task_msgs --symlink-install
    # 将 workspace 的 setup.bash 添加到 ~/.bashrc
    local_setup="$(pwd)/install/setup.bash"
    grep -qxF "source $local_setup" ~/.bashrc 2>/dev/null \
        || echo "source $local_setup" >> ~/.bashrc
    source "$local_setup"
    cd "$ROOT_DIR"
    echo "  ✓ ROS2 工作空间构建完成"
elif [ "$WITH_ROS" = true ]; then
    echo "[3/6] 跳过 ROS2 构建（ros_workspace 目录不存在）"
else
    echo "[3/6] 跳过 ROS2 构建（--no-ros）"
fi

# ──────────────────────────────────────────────
# 4. Python 虚拟环境 + 安装依赖
# ──────────────────────────────────────────────
echo "[4/6] 配置 Python 虚拟环境..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv --system-site-packages venv
    echo "  ✓ 虚拟环境已创建"
else
    echo "  ✓ 虚拟环境已存在，跳过创建"
fi

source venv/bin/activate
pip install --upgrade pip setuptools wheel -q
echo "  ✓ pip 已升级"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    echo "  ✓ Python 依赖已安装"
fi

cd "$ROOT_DIR"

# ──────────────────────────────────────────────
# 5. 初始化数据库 + 种子数据
# ──────────────────────────────────────────────
echo "[5/6] 初始化数据库..."
cd "$BACKEND_DIR"
source venv/bin/activate

if python -m database.scripts.init_db; then
    echo "  ✓ 数据库表结构已创建"
else
    echo "  ⚠ 建表失败，请检查数据库配置"
fi

if [ -f "pharmacy.db" ]; then
    echo "  ✓ 数据库文件: $(ls -lh pharmacy.db | awk '{print $5}')"
fi

if python -m database.scripts.seed_drugs; then
    echo "  ✓ 药品种子数据已填充"
else
    echo "  ⚠ 药品数据填充失败"
fi

if python -m database.scripts.seed_users; then
    echo "  ✓ 演示用户已创建"
else
    echo "  ⚠ 演示用户创建失败"
fi

cd "$ROOT_DIR"

# ──────────────────────────────────────────────
# 6. .env 配置检查
# ──────────────────────────────────────────────
echo "[6/6] 检查 .env 配置文件..."

if [ ! -f "$BACKEND_DIR/.env" ]; then
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        echo ""
        echo "  ╔══════════════════════════════════════════╗"
        echo "  ║   ⚠ 未检测到 .env 文件                   ║"
        echo "  ║                                          ║"
        echo "  ║  请执行以下命令创建配置文件：              ║"
        echo "  ║                                          ║"
        echo "  ║  cp agent_with_backend/.env.example \\    ║"
        echo "  ║     agent_with_backend/.env              ║"
        echo "  ║  vim agent_with_backend/.env             ║"
        echo "  ║                                          ║"
        echo "  ║  然后根据注释填写你的配置项                ║"
        echo "  ╚══════════════════════════════════════════╝"
        echo ""
    else
        echo "  ⚠ 未找到 .env.example 模板文件"
    fi
else
    echo "  ✓ .env 文件已存在"
fi

# ──────────────────────────────────────────────
echo ""
echo "============================================"
echo "  ✅ 环境配置完成！"
echo ""
if [ "$WITH_ROS" = true ]; then
    echo "  ROS2 工作空间 : $ROS_WS_DIR"
fi
echo "  虚拟环境     : $BACKEND_DIR/venv"
echo "  数据库       : $BACKEND_DIR/pharmacy.db"
echo ""
echo "  接下来每次启动系统请运行："
echo ""
echo "    cd agent_with_backend && ./quick_start.sh"
echo ""
echo "============================================"
