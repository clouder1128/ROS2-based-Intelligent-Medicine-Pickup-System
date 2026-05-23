"""
状态订阅器 - 订阅Unity仿真状态消息
将ROS2状态消息转换为backend格式，更新数据库
"""

import threading
import time
import sqlite3
from typing import Dict, Any, Optional
from .config import Config, TopicConfig
from .node_manager import RosNodeManager
from .message_adapter import MessageAdapter
from .error_handler import ErrorHandler
from common.utils.database import get_db_connection
from common.utils.debug_logger import debug_log

# 条件导入ROS2模块
try:
    import rclpy
    from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    rclpy = None

class StateSubscriber:
    """
    状态订阅器 - 订阅任务状态、车辆状态、药柜状态
    """

    def __init__(self):
        """初始化状态订阅器"""
        self._config = Config()
        self._node_manager = RosNodeManager.get_instance()
        self._message_adapter = MessageAdapter()
        self._error_handler = ErrorHandler()

        # 订阅器实例
        self._task_state_subscriber = None
        self._car_state_subscriber = None
        self._cabinet_state_subscriber = None

        # 回调函数
        self._task_state_callback = None
        self._car_state_callback = None
        self._cabinet_state_callback = None

        self._initialized = False

        self._init_subscribers()

    def _init_subscribers(self):
        """初始化ROS2订阅器"""
        if not ROS2_AVAILABLE:
            print("[StateSubscriber] ROS2 not available, using fallback mode")
            return

        try:
            node = self._node_manager.get_node()
            if node is None:
                print("[StateSubscriber] ROS2 node not available")
                return

            # 配置QoS
            qos_profile = QoSProfile(
                depth=TopicConfig.QOS_DEPTH,
                reliability=QoSReliabilityPolicy.RELIABLE,
                durability=QoSDurabilityPolicy.VOLATILE
            )

            # 导入消息类型
            try:
                from task_msgs.msg import TaskState
                from task_msgs.msg import CarState
                from task_msgs.msg import CabinetState

                # 创建任务状态订阅器
                self._task_state_subscriber = node.create_subscription(
                    TaskState,
                    TopicConfig.TASK_STATE_TOPIC,
                    self._task_state_callback_wrapper,
                    qos_profile
                )

                # 创建车辆状态订阅器
                self._car_state_subscriber = node.create_subscription(
                    CarState,
                    TopicConfig.CAR_STATE_TOPIC,
                    self._car_state_callback_wrapper,
                    qos_profile
                )

                # 创建药柜状态订阅器
                self._cabinet_state_subscriber = node.create_subscription(
                    CabinetState,
                    TopicConfig.CABINET_STATE_TOPIC,
                    self._cabinet_state_callback_wrapper,
                    qos_profile
                )

                self._initialized = True
                print("[StateSubscriber] Initialized with all topic subscribers")

            except ImportError as e:
                print(f"[StateSubscriber] Message types not available: {e}")

        except Exception as e:
            print(f"[StateSubscriber] Failed to initialize subscribers: {e}")

    def set_task_state_callback(self, callback):
        """设置任务状态回调函数"""
        self._task_state_callback = callback

    def set_car_state_callback(self, callback):
        """设置车辆状态回调函数"""
        self._car_state_callback = callback

    def set_cabinet_state_callback(self, callback):
        """设置药柜状态回调函数"""
        self._cabinet_state_callback = callback

    def _task_state_callback_wrapper(self, msg):
        """任务状态回调包装器 - 写入 RosStateStore 和数据库"""
        try:
            from ros_integration.state_store import RosStateStore
            store = RosStateStore()
            task_id = str(msg.taskid) if hasattr(msg, 'taskid') else "0"
            task_state = int(msg.task_state) if hasattr(msg, 'task_state') else 0
            car_id = int(msg.car_id) if hasattr(msg, 'car_id') else 0
            store.update_task(task_id, task_state, car_id)

            state_name = {0: 'pending', 1: 'in_progress', 2: 'delivered', 3: 'failed'}.get(task_state, 'unknown')
            debug_log("[ROS←SUB]", "TASK",
                      f"task_id={task_id} state={task_state}({state_name}) car={car_id}")

            # 更新数据库中的订单状态和审批跟踪状态
            if task_state >= 1:
                try:
                    conn = get_db_connection()
                    # task_state=1 → in_progress, =2 → delivered, =3 → failed
                    tracking_map = {1: 'in_progress', 2: 'delivered', 3: 'failed'}
                    tracking_status = tracking_map.get(task_state)
                    if tracking_status:
                        conn.execute(
                            "UPDATE approvals SET tracking_status = ? WHERE task_id = ? "
                            "AND tracking_status IN ('pending_dispatch', 'in_progress', 'delivered')",
                            (tracking_status, task_id),
                        )

                    # 任务进行中时更新 order_log
                    if task_state == 1:
                        conn.execute(
                            "UPDATE order_log SET status = 'in_progress' WHERE task_id = ? AND status = 'pending'",
                            (int(task_id),),
                        )

                    # 任务完成或失败时更新 order_log
                    if task_state >= 2:
                        new_status = "failed" if task_state == 3 else "delivered"
                        conn.execute(
                            "UPDATE order_log SET status = ? WHERE task_id = ? AND status IN ('pending', 'in_progress')",
                            (new_status, int(task_id)),
                        )

                    # 构建 order_log 状态描述
                    if task_state == 1:
                        order_status_desc = "in_progress"
                    elif task_state >= 2:
                        order_status_desc = new_status
                    else:
                        order_status_desc = "unchanged"

                    conn.commit()
                    debug_log("[STATE]", "DB_UPDATE",
                              f"task_id={task_id}",
                              f"tracking={tracking_status} order={order_status_desc}")
                    conn.close()
                except Exception as db_e:
                    err_msg = str(db_e)
                    debug_log("[STATE!]", "DB_UPDATE",
                              f"task_id={task_id}",
                              f"error={err_msg}")
                    # 自动修复: approvals 表缺少 tracking_status 列时补充迁移
                    if "no such column: tracking_status" in err_msg:
                        try:
                            conn2 = get_db_connection()
                            conn2.execute(
                                "ALTER TABLE approvals ADD COLUMN tracking_status TEXT DEFAULT 'waiting_approval'"
                            )
                            conn2.commit()
                            conn2.close()
                            debug_log("[STATE]", "DB_MIGRATE",
                                      "approvals.tracking_status",
                                      "auto-migrated")
                        except Exception as migrate_e:
                            debug_log("[STATE!]", "DB_MIGRATE",
                                      "approvals.tracking_status",
                                      f"failed: {migrate_e}")
                    else:
                        print(f"[StateSubscriber] Failed to update database: {db_e}")
        except Exception as e:
            print(f"[StateSubscriber] Error in task state store update: {e}")
        if self._task_state_callback is not None:
            try:
                # 转换消息格式
                backend_state = self._message_adapter.unity_to_backend(msg)
                self._task_state_callback(backend_state)
            except Exception as e:
                print(f"[StateSubscriber] Error in task state callback: {e}")
                self._error_handler.handle_publish_error(e, task_id=None, retry_strategy="none")

    def _car_state_callback_wrapper(self, msg):
        """车辆状态回调包装器 - 写入 RosStateStore"""
        try:
            from ros_integration.state_store import RosStateStore
            store = RosStateStore()
            car_id = int(msg.car_id) if hasattr(msg, 'car_id') else 0
            x = float(msg.x) if hasattr(msg, 'x') else 0.0
            y = float(msg.y) if hasattr(msg, 'y') else 0.0
            isrunning = int(msg.isrunning) if hasattr(msg, 'isrunning') else 0
            store.update_car(car_id, x, y, isrunning)
            debug_log("[ROS←SUB]", "CAR",
                      f"car_id={car_id} pos=({x:.1f},{y:.1f})",
                      f"running={isrunning}")
        except Exception as e:
            print(f"[StateSubscriber] Error in car state callback: {e}")
        if self._car_state_callback is not None:
            try:
                self._car_state_callback(msg)
            except Exception as e:
                print(f"[StateSubscriber] Error in car state user callback: {e}")

    def _cabinet_state_callback_wrapper(self, msg):
        """药柜状态回调包装器 - 写入 RosStateStore"""
        try:
            from ros_integration.state_store import RosStateStore
            store = RosStateStore()
            cabinet_id = int(msg.cabinet_id) if hasattr(msg, 'cabinet_id') else 0
            medicine_list = []
            if hasattr(msg, 'medicine_list'):
                for md in msg.medicine_list:
                    medicine_list.append({
                        "row": int(md.row) if hasattr(md, 'row') else 0,
                        "column": int(md.column) if hasattr(md, 'column') else 0,
                        "count": int(md.count) if hasattr(md, 'count') else 0,
                    })
            store.update_cabinet(cabinet_id, medicine_list)
            debug_log("[ROS←SUB]", "CABINET",
                      f"cabinet={cabinet_id}",
                      f"items={len(medicine_list)}")
        except Exception as e:
            print(f"[StateSubscriber] Error in cabinet state callback: {e}")
        if self._cabinet_state_callback is not None:
            try:
                self._cabinet_state_callback(msg)
            except Exception as e:
                print(f"[StateSubscriber] Error in cabinet state user callback: {e}")

    def is_initialized(self):
        """检查订阅器是否初始化"""
        return self._initialized

    def start(self):
        """启动订阅器（实际不需要，由ROS2执行器处理）"""
        if not self._initialized:
            print("[StateSubscriber] Not initialized, cannot start")
            return False
        print("[StateSubscriber] Started (running in ROS2 executor)")
        return True