#!/usr/bin/env bash
#
# quick_start.sh - 一键启动智能药品管理系统
# 自动初始化数据库、启动后端和前端的静态服务器。
#
# 用法:
#   ./quick_start.sh
#
# 用 Ctrl+C 停止所有服务。
#

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
WEB_DIR="${ROOT_DIR}/web"
DB_FILE="${ROOT_DIR}/pharmacy.db"
BACKEND_PORT=8001
FRONTEND_PORT=8080
BACKEND_PID=""
FRONTEND_PID=""

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cleanup() {
    echo ""
    echo -e "${YELLOW}[停止] 正在关闭服务...${NC}"
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && echo "  - 后端服务已停止"
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && echo "  - 前端服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "============================================"
echo "  智能药品管理系统 - 一键启动"
echo "============================================"
echo ""

# ---- 检查 Python ----
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[错误] 未找到 python3，请先安装 Python 3.8+${NC}"
    exit 1
fi

# ---- 检查依赖 ----
if ! python3 -c "import flask, flask_cors, jwt" 2>/dev/null; then
    echo -e "${YELLOW}[安装] 安装 Python 依赖...${NC}"
    pip3 install -r "${ROOT_DIR}/requirements.txt" --quiet
    echo -e "${GREEN}[完成] 依赖安装完成${NC}"
fi

# ---- 检查端口占用 ----
for port in $BACKEND_PORT $FRONTEND_PORT; do
    if lsof -i :$port &>/dev/null 2>&1; then
        echo -e "${RED}[错误] 端口 $port 已被占用，请先关闭占用进程${NC}"
        echo "  使用: lsof -i :$port 查看占用进程"
        exit 1
    fi
done

# ---- 清理持久化会话状态 ----
SESSION_DIR="${ROOT_DIR}/sessions"
if [ -d "$SESSION_DIR" ]; then
    echo -e "${YELLOW}[清理] 清除持久化会话状态...${NC}"
    rm -f "${SESSION_DIR}"/*.pkl
    echo -e "${GREEN}  - 会话状态已重置${NC}"
fi

# ---- 初始化数据库 ----
if [ ! -f "$DB_FILE" ]; then
    echo -e "${YELLOW}[初始化] 数据库不存在，正在创建...${NC}"
    (cd "$ROOT_DIR" && python3 -m database.scripts.init_db) && \
        echo -e "${GREEN}  - 表结构创建完成${NC}" || \
        { echo -e "${RED}  - 表结构创建失败${NC}"; exit 1; }
else
    echo -e "${GREEN}[跳过] 数据库已存在${NC}"
fi

# ---- 启动后端 ----
echo -e "${YELLOW}[启动] 后端服务 (端口 $BACKEND_PORT)...${NC}"
(cd "$ROOT_DIR" && python3 main.py) &
BACKEND_PID=$!

# 等待后端就绪（最多等 10 秒，健康检查返回 200）
echo -e "  - 等待后端就绪...${NC}"
for i in $(seq 1 10); do
    if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$BACKEND_PORT/api/health" 2>/dev/null | grep -q 200; then
        echo -e "${GREEN}  - 后端服务已启动 (PID: $BACKEND_PID)${NC}"
        break
    fi
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${RED}[错误] 后端服务启动失败${NC}"
        cleanup
    fi
    sleep 1
done

# ---- 种子数据 ----
# 务必在"后端启动后"执行 seed_users，因为 auth 表由后端 ensure_auth_schema() 创建
echo -e "${YELLOW}[初始化] 填充演示用户...${NC}"
(cd "$ROOT_DIR" && python3 -m database.scripts.seed_users) && \
    echo -e "${GREEN}  - 演示用户创建完成${NC}" || \
    echo -e "${RED}  - 演示用户创建失败，可稍后手动运行${NC}"

echo -e "${YELLOW}[初始化] 填充演示药品数据...${NC}"
(cd "$ROOT_DIR" && python3 -m database.scripts.seed_drugs) && \
    echo -e "${GREEN}  - 演示药品数据创建完成${NC}" || \
    echo -e "${RED}  - 演示药品数据创建失败，可稍后手动运行${NC}"

# ---- 启动前端 ----
echo -e "${YELLOW}[启动] 前端静态服务 (端口 $FRONTEND_PORT)...${NC}"
(cd "$WEB_DIR" && python3 -m http.server "$FRONTEND_PORT") &
FRONTEND_PID=$!
sleep 1

if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo -e "${RED}[错误] 前端服务启动失败${NC}"
    cleanup
fi
echo -e "${GREEN}  - 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

# ---- 打开浏览器 ----
echo ""
echo "============================================"
echo -e "${GREEN}  系统启动成功！${NC}"
echo ""
echo "  前端地址: http://localhost:$FRONTEND_PORT"
echo "  后端地址: http://localhost:$BACKEND_PORT/api/health"
echo ""
echo "  演示账号:"
echo "    患者:   patient1 / 123456"
echo "    医生:   doctor1 / 123456"
echo "    管理员: admin1  / 123456"
echo ""
echo "  按 Ctrl+C 停止全部服务"
echo "============================================"

# 尝试打开浏览器
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:$FRONTEND_PORT" 2>/dev/null &
elif command -v open &>/dev/null; then
    open "http://localhost:$FRONTEND_PORT" 2>/dev/null &
fi

# 等待子进程
wait
