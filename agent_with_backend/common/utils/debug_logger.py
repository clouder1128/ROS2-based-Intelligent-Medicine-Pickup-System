"""
调试日志工具 - 终端彩色高亮显示关键操作记录
通过 DEBUG_MODE 环境变量控制：DEBUG_MODE=0 关闭，默认开启

显示过滤：
  DEBUG_MODE=1  仅显示 [STATE] / [STATE!] 类别的日志（默认）
  DEBUG_ALL=1   显示所有类别日志（还原全部输出）
"""

import os
import sys
from datetime import datetime

# ANSI 转义码
_CYAN = "\033[36m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_RESET = "\033[0m"

# 类别 → 颜色映射
_CATEGORY_COLORS = {
    "[APPROVAL]": _CYAN,
    "[ORDER]": _MAGENTA,
    "[ROS→PUB]": _BLUE,
    "[ROS←SUB]": _YELLOW,
    "[STATE]": _GREEN,
    "[STATE!]": _RED,
}

# 非 verbose 模式下仅允许显示的类别前缀
_DEFAULT_ALLOWED = {"[STATE]", "[STATE!]"}


def _enabled() -> bool:
    return os.getenv("DEBUG_MODE", "1") == "1"


def _is_allowed(category: str) -> bool:
    """判断该类别是否允许输出。DEBUG_ALL=1 时全部放行。"""
    if os.getenv("DEBUG_ALL") == "1":
        return True
    return category in _DEFAULT_ALLOWED


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:12]


def debug_log(category: str, operation: str, detail: str, result: str = "") -> None:
    """输出彩色调试日志到 stderr

    Args:
        category: 分类标签，如 '[APPROVAL]', '[ORDER]', '[ROS→PUB]'
        operation: 操作名称，如 'CREATE', 'APPROVE', 'TASK'
        detail: 操作详情
        result: 可选的执行结果/状态
    """
    if not _enabled():
        return
    if not _is_allowed(category):
        return

    color = _CATEGORY_COLORS.get(category, _RESET)
    ts = _timestamp()
    parts = [f"{color}{ts} {category}·{operation}{_RESET}  {detail}"]
    if result:
        parts.append(f" → {result}")

    print(*parts, file=sys.stderr, flush=True)
