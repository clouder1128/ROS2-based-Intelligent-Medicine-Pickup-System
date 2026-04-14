"""
ROS2 集成模块 - 替代原有的ros2_bridge.py
提供与Unity仿真的完整双向通信功能
"""

# 基础配置模块始终可用
from .config import Config, TopicConfig

# 其他模块可能尚未创建，使用条件导入
try:
    from .node_manager import RosNodeManager
except ImportError:
    RosNodeManager = None

try:
    from .task_publisher import TaskPublisher
except ImportError:
    TaskPublisher = None

try:
    from .state_subscriber import StateSubscriber
except ImportError:
    StateSubscriber = None

try:
    from .message_adapter import MessageAdapter
except ImportError:
    MessageAdapter = None

try:
    from .error_handler import ErrorHandler, GracefulDegradation
except ImportError:
    ErrorHandler = None
    GracefulDegradation = None

try:
    from .health_monitor import HealthMonitor
except ImportError:
    HealthMonitor = None

__version__ = "1.0.0"
__all__ = [
    "Config",
    "TopicConfig",
    "RosNodeManager",
    "TaskPublisher",
    "StateSubscriber",
    "MessageAdapter",
    "ErrorHandler",
    "GracefulDegradation",
    "HealthMonitor",
]