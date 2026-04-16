"""
ROS2节点管理器 - 统一管理ROS2节点生命周期
避免多次rclpy.init()冲突，提供线程安全访问
"""

import threading
import time
import atexit
import os
from typing import Optional, Any
from .config import Config

class RosNodeManager:
    """
    ROS2节点管理器（单例模式）
    负责ROS2节点的初始化、执行器管理和优雅关闭
    """

    _instance: Optional['RosNodeManager'] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'RosNodeManager':
        """获取单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        """私有构造函数"""
        self._node = None
        self._executor = None
        self._executor_thread = None
        self._shutdown_requested = False
        self._config = Config()
        self._initialized = False

        self._init_ros2()
        self._initialized = True

        # 注册退出处理
        atexit.register(self._atexit_shutdown)

    def _init_ros2(self):
        """初始化ROS2（线程安全）"""
        try:
            import rclpy
            from rclpy.executors import MultiThreadedExecutor

            # 避免重复初始化
            if not rclpy.ok():
                rclpy.init()
                print(f"[ROS2] Initialized with domain ID: {self._config.ROS_DOMAIN_ID}")

            # 创建节点
            self._node = rclpy.create_node(self._config.ROS_NODE_NAME)

            # 创建执行器
            num_threads = min(4, self._get_optimal_thread_count())
            self._executor = MultiThreadedExecutor(num_threads=num_threads)
            self._executor.add_node(self._node)

            print(f"[ROS2] Node '{self._config.ROS_NODE_NAME}' created with {num_threads} threads")

        except Exception as e:
            print(f"[ROS2] Failed to initialize: {e}")
            self._node = None
            self._executor = None

    def _get_optimal_thread_count(self) -> int:
        """获取最优线程数"""
        cpu_count = os.cpu_count() or 2
        return min(cpu_count, 8)  # 最多8个线程

    def start(self):
        """启动节点管理器（非阻塞）"""
        if self._executor is None or self._node is None:
            print("[ROS2] Cannot start: ROS2 not initialized")
            return

        if self._executor_thread is not None and self._executor_thread.is_alive():
            print("[ROS2] Already started")
            return

        # 创建后台线程运行执行器
        self._executor_thread = threading.Thread(
            target=self._executor_thread_func,
            daemon=True,
            name="ros2_executor"
        )
        self._shutdown_requested = False
        self._executor_thread.start()

        print("[ROS2] Node manager started")

    def _executor_thread_func(self):
        """执行器线程函数"""
        import rclpy

        try:
            while rclpy.ok() and not self._shutdown_requested:
                self._executor.spin_once(timeout_sec=0.1)
        except Exception as e:
            print(f"[ROS2] Executor thread error: {e}")
        finally:
            print("[ROS2] Executor thread stopped")

    def shutdown(self):
        """优雅关闭节点管理器"""
        if self._shutdown_requested:
            return

        print("[ROS2] Shutting down node manager...")
        self._shutdown_requested = True

        # 等待执行器线程结束
        if self._executor_thread is not None and self._executor_thread.is_alive():
            self._executor_thread.join(timeout=5.0)

        # 清理资源
        if self._executor is not None:
            self._executor.shutdown()

        if self._node is not None:
            self._node.destroy_node()

        import rclpy
        if rclpy.ok():
            rclpy.shutdown()

        print("[ROS2] Node manager shutdown complete")

    def _atexit_shutdown(self):
        """程序退出时的清理"""
        if not self._shutdown_requested:
            self.shutdown()

    def is_running(self) -> bool:
        """检查节点是否在运行"""
        if self._executor_thread is None:
            return False
        return self._executor_thread.is_alive()

    def get_node(self):
        """获取ROS2节点实例"""
        return self._node

    def get_executor(self):
        """获取执行器实例"""
        return self._executor

    def check_connection(self) -> bool:
        """检查ROS2连接状态"""
        import rclpy
        return rclpy.ok() and self._node is not None and self.is_running()