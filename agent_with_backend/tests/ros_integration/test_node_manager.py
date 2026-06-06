"""RosNodeManager 节点管理器单元测试

测试依赖于 conftest.py 中注入的 rclpy / rclpy.executors mock。
每次运行前通过 reset_singletons fixture 重置 RosNodeManager._instance。
"""

import pytest
from unittest.mock import MagicMock, patch
from ros_integration.node_manager import RosNodeManager


class TestSingleton:
    def test_get_instance_returns_same(self):
        nm1 = RosNodeManager.get_instance()
        nm2 = RosNodeManager.get_instance()
        assert nm1 is nm2

    def test_get_instance_creates_on_demand(self):
        RosNodeManager._instance = None
        nm = RosNodeManager.get_instance()
        assert nm is not None


class TestInitRos2:
    def test_init_creates_node_and_executor(self):
        RosNodeManager._instance = None
        nm = RosNodeManager.get_instance()
        # _init_ros2 已被 __init__ 调用过
        assert nm._node is not None
        assert nm._executor is not None

    def test_init_registers_atexit(self):
        RosNodeManager._instance = None
        nm = RosNodeManager.get_instance()
        assert hasattr(nm, "_atexit_shutdown")


class TestCheckConnection:
    def test_check_connection_returns_true_when_ok(self):
        RosNodeManager._instance = None
        nm = RosNodeManager.get_instance()
        # rclpy.ok() 返回 True, _node 不为 None, 线程未运行但 is_running 返回 False
        # 所以 check_connection 将返回 False（is_running 为 False）
        import rclpy
        rclpy.ok.return_value = True
        nm._node = MagicMock()
        # check_connection 需要 is_running() == True
        nm._executor_thread = MagicMock()
        nm._executor_thread.is_alive.return_value = True
        assert nm.check_connection() is True

    def test_check_connection_false_when_rclpy_not_ok(self):
        import rclpy
        rclpy.ok.return_value = False
        nm = RosNodeManager.get_instance()
        nm._node = MagicMock()
        nm._executor_thread = MagicMock()
        nm._executor_thread.is_alive.return_value = True
        assert nm.check_connection() is False


class TestStartShutdown:
    def test_start_creates_executor_thread(self):
        nm = RosNodeManager.get_instance()
        nm._executor = MagicMock()
        nm._node = MagicMock()
        nm._executor_thread = None
        nm.start()
        assert nm._executor_thread is not None
        assert nm._executor_thread.name == "ros2_executor"
        assert nm._executor_thread.daemon is True

    def test_shutdown_stops_executor_thread(self):
        nm = RosNodeManager.get_instance()
        nm._executor = MagicMock()
        nm._node = MagicMock()
        nm._executor_thread = MagicMock()
        nm._executor_thread.is_alive.return_value = False
        nm._shutdown_requested = False
        nm.shutdown()
        assert nm._shutdown_requested is True

    def test_is_running_false_when_no_thread(self):
        nm = RosNodeManager.get_instance()
        nm._executor_thread = None
        assert nm.is_running() is False

    def test_is_running_true_when_alive(self):
        nm = RosNodeManager.get_instance()
        nm._executor_thread = MagicMock()
        nm._executor_thread.is_alive.return_value = True
        assert nm.is_running() is True


class TestGetNodeAndExecutor:
    def test_get_node_returns_node(self):
        nm = RosNodeManager.get_instance()
        nm._node = "mock_node"
        assert nm.get_node() == "mock_node"

    def test_get_executor_returns_executor(self):
        nm = RosNodeManager.get_instance()
        nm._executor = "mock_executor"
        assert nm.get_executor() == "mock_executor"


class TestOptimalThreadCount:
    def test_get_optimal_thread_count(self):
        nm = RosNodeManager.get_instance()
        count = nm._get_optimal_thread_count()
        assert 1 <= count <= 8
