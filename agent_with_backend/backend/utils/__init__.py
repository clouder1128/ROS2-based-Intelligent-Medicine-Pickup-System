"""
Utility functions and modules
"""

# 保持现有导出
from .database import get_db_connection, close_db_connection
from .drug_helpers import validate_and_get_drug, find_drug_id_by_name
from .logger import setup_logger, get_logger
from .ros2_bridge import publish_task, publish_expiry_removal, check_ros2_status

# 新增ROS2集成模块导出
try:
    from ..ros_integration import (
        Config as RosConfig,
        TopicConfig,
        RosNodeManager,
        TaskPublisher,
        StateSubscriber,
        MessageAdapter,
        ErrorHandler,
        GracefulDegradation,
        HealthMonitor,
    )
except ImportError:
    # 新模块未安装时跳过
    pass

__all__ = [
    "get_db_connection",
    "close_db_connection",
    "validate_and_get_drug",
    "find_drug_id_by_name",
    "setup_logger",
    "get_logger",
    "publish_task",
    "publish_expiry_removal",
    "check_ros2_status",
]