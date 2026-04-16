"""节点管理器测试"""

import pytest
import threading
import time
from unittest.mock import Mock, patch
from backend.ros_integration.node_manager import RosNodeManager
from backend.ros_integration.config import Config

def test_node_manager_singleton():
    """测试节点管理器单例模式"""
    manager1 = RosNodeManager.get_instance()
    manager2 = RosNodeManager.get_instance()

    assert manager1 is manager2
    assert manager1 == manager2

def test_node_manager_initialization():
    """测试节点管理器初始化"""
    manager = RosNodeManager.get_instance()

    # 重置实例以测试初始化
    RosNodeManager._instance = None

    with patch('rclpy.init') as mock_init:
        with patch('rclpy.ok', return_value=False):
            manager = RosNodeManager.get_instance()

            # 验证rclpy.init被调用
            mock_init.assert_called_once()

    # 清理
    RosNodeManager._instance = None

def test_node_manager_already_initialized():
    """测试ROS2已初始化时的处理"""
    manager = RosNodeManager.get_instance()
    RosNodeManager._instance = None

    with patch('rclpy.ok', return_value=True):
        with patch('rclpy.init') as mock_init:
            manager = RosNodeManager.get_instance()

            # rclpy.init不应被调用
            mock_init.assert_not_called()

    # 清理
    RosNodeManager._instance = None

def test_node_manager_start_stop():
    """测试节点启动和停止"""
    manager = RosNodeManager.get_instance()
    RosNodeManager._instance = None

    with patch('threading.Thread') as mock_thread_class:
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        manager = RosNodeManager.get_instance()
        manager.start()

        # 验证线程启动
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()

        # 测试关闭
        with patch('rclpy.shutdown') as mock_shutdown:
            manager.shutdown()
            mock_shutdown.assert_called_once()

    # 清理
    RosNodeManager._instance = None

def test_node_manager_thread_safety():
    """测试节点管理器线程安全"""
    manager = RosNodeManager.get_instance()
    RosNodeManager._instance = None

    results = []

    def create_manager(index):
        try:
            manager = RosNodeManager.get_instance()
            results.append((index, manager))
        except Exception as e:
            results.append((index, e))

    # 创建多个线程同时获取实例
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_manager, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # 验证所有线程得到同一个实例
    instances = [r[1] for r in results if not isinstance(r[1], Exception)]
    assert len(instances) == 5
    assert all(inst is instances[0] for inst in instances)

    # 清理
    RosNodeManager._instance = None