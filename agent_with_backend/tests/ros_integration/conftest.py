"""ROS2 集成模块测试 — conftest

在导入 ros_integration 前向 sys.modules 注入 ROS2 / task_msgs / std_msgs 的 mock，
使 ros_integration 各模块在无真实 ROS2 环境的条件下仍能正常导入。

同时提供重置单例的 fixture，保证 test isolation。
"""

import os
import sys
import importlib
from unittest.mock import MagicMock

# ── 将项目根目录加入 sys.path ──────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# ── 在 ros_integration 被导入前注入 mock 模块 ─────────────────
# 顺序重要：先建立 sys.modules 再执行任何 from ros_integration import

# 1. rclpy（核心 ROS2 客户端库）
_mock_rclpy = MagicMock()
_mock_rclpy.ok.return_value = True
sys.modules["rclpy"] = _mock_rclpy

# rclpy.qos
_mock_rclpy_qos = MagicMock()
_mock_rclpy_qos.QoSProfile = MagicMock
_mock_rclpy_qos.QoSReliabilityPolicy = MagicMock()
_mock_rclpy_qos.QoSDurabilityPolicy = MagicMock()
sys.modules["rclpy.qos"] = _mock_rclpy_qos

# rclpy.executors
_mock_rclpy_executors = MagicMock()
_mock_rclpy_executors.MultiThreadedExecutor = MagicMock
sys.modules["rclpy.executors"] = _mock_rclpy_executors

# 2. task_msgs.msg（自定义 ROS2 消息类型）
_mock_task_msgs_msg = MagicMock()
_mock_task_msgs_msg.Task = MagicMock
_mock_task_msgs_msg.CabinetOrder = MagicMock
_mock_task_msgs_msg.MedicineData = MagicMock
_mock_task_msgs_msg.TaskState = MagicMock
_mock_task_msgs_msg.CarState = MagicMock
_mock_task_msgs_msg.CabinetState = MagicMock
sys.modules["task_msgs"] = MagicMock()
sys.modules["task_msgs.msg"] = _mock_task_msgs_msg

# 3. std_msgs.msg（标准 ROS2 消息类型）
_mock_std_msgs_msg = MagicMock()
_mock_std_msgs_msg.String = MagicMock
sys.modules["std_msgs"] = MagicMock()
sys.modules["std_msgs.msg"] = _mock_std_msgs_msg

# API tests may import ROS modules before this directory's conftest is loaded.
# Reload the publisher after installing the fake ROS packages so its optional
# imports and message classes consistently point at these test doubles.
if "ros_integration.task_publisher" in sys.modules:
    importlib.reload(sys.modules["ros_integration.task_publisher"])

import pytest
from ros_integration.state_store import RosStateStore
from ros_integration.node_manager import RosNodeManager
from ros_integration.message_adapter import MessageAdapter


@pytest.fixture(autouse=True)
def reset_singletons():
    """每个测试前重置所有单例和模块级全局变量，保证 test isolation。"""
    # 重置 ros_integration 包内的单例
    RosStateStore._instance = None
    RosNodeManager._instance = None
    MessageAdapter._instance = None

    # 重置 bridge.py 模块级全局变量
    import ros_integration.bridge as bridge_mod

    bridge_mod.ros2_available = False
    bridge_mod.task_publisher_instance = None
    bridge_mod.shutdown_requested = False

    yield

    # 善后
    RosStateStore._instance = None
    RosNodeManager._instance = None
    MessageAdapter._instance = None

    bridge_mod.ros2_available = False
    bridge_mod.task_publisher_instance = None
    bridge_mod.shutdown_requested = False
