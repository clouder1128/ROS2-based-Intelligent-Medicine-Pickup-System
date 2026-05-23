#!/usr/bin/env python3
"""
仿真消息发布者 - 模拟仿真端发布车辆状态、药柜状态、药柜运行状态和任务状态
用于测试 send_receive_ros_msg.py 节点的接收功能
"""

import rclpy
from rclpy.node import Node
from rclpy import qos
import random
import time

class SimulationPublisher(Node):
    def __init__(self):
        super().__init__('simulation_publisher')

        # 初始化消息类型
        self.init_message_types()

        # 创建四个发布者
        self.car_state_pub = self.create_publisher(
            self.CarState,
            '/CarState_U',
            qos.qos_profile_system_default
        )

        self.cabinet_state_pub = self.create_publisher(
            self.CabinetState,
            '/CabinetState_U',
            qos.qos_profile_system_default
        )

        self.cabinet_running_pub = self.create_publisher(
            self.CabinetRunning,
            '/CabinetRunning_U',
            qos.qos_profile_system_default
        )

        self.task_state_pub = self.create_publisher(
            self.TaskState,
            '/TaskState_U',
            qos.qos_profile_system_default
        )

        self.task_data_pub = self.create_publisher(
            self.Task,
            '/TaskData_U',
            qos.qos_profile_system_default
        )

        # 定时器：每2秒发布所有消息
        self.publish_timer = self.create_timer(2.0, self.publish_all_messages)

        # 初始化状态数据
        self.car_id = 1
        self.car_x = 0.0
        self.car_y = 0.0
        self.car_isrunning = 1

        self.cabinet_id = 1
        self.cabinet_isrunning = 1

        self.task_counter = 1001
        self.task_state = 0  # 0:等待, 1:执行中, 2:完成

        self.get_logger().info('仿真消息发布者已启动')
        self.get_logger().info('将发布以下主题：')
        self.get_logger().info('  - /CarState_U (车辆状态)')
        self.get_logger().info('  - /CabinetState_U (药柜状态)')
        self.get_logger().info('  - /CabinetRunning_U (药柜运行状态)')
        self.get_logger().info('  - /TaskState_U (任务状态)')
        self.get_logger().info('  - /TaskData_U (完整任务数据)')

    def init_message_types(self):
        """初始化消息类型"""
        try:
            from task_msgs.msg import CarState, CabinetState, CabinetRunning, TaskState, Task, CabinetOrder, MedicineData
            self.CarState = CarState
            self.CabinetState = CabinetState
            self.CabinetRunning = CabinetRunning
            self.TaskState = TaskState
            self.Task = Task
            self.CabinetOrder = CabinetOrder
            self.MedicineData = MedicineData
        except ImportError as e:
            self.get_logger().error(f"消息类型导入失败: {e}")
            raise

    def publish_all_messages(self):
        """发布所有仿真消息"""
        self.publish_car_state()
        self.publish_cabinet_state()
        self.publish_cabinet_running()
        self.publish_task_state()
        self.publish_task_data()

    def publish_car_state(self):
        """发布车辆状态"""
        msg = self.CarState()

        # 模拟车辆移动
        self.car_x += random.uniform(-1.0, 1.0)
        self.car_y += random.uniform(-1.0, 1.0)
        self.car_isrunning = random.choice([0, 1])

        msg.car_id = self.car_id
        msg.x = float(round(self.car_x, 2))
        msg.y = float(round(self.car_y, 2))
        msg.isrunning = self.car_isrunning

        self.car_state_pub.publish(msg)
        self.get_logger().debug(f"发布车辆状态: 车辆{msg.car_id} 位置({msg.x}, {msg.y}) 运行状态{msg.isrunning}")

    def publish_cabinet_state(self):
        """发布药柜状态"""
        msg = self.CabinetState()

        # 随机选择药柜ID (1-5)
        self.cabinet_id = random.randint(1, 5)
        msg.cabinet_id = self.cabinet_id

        # 随机生成药品列表 (1-5个药品)
        medicine_list = []
        num_medicines = random.randint(1, 5)

        for i in range(num_medicines):
            medicine = self.MedicineData()
            medicine.row = random.randint(1, 10)
            medicine.column = random.randint(1, 10)
            medicine.count = random.randint(1, 20)
            medicine_list.append(medicine)

        msg.medicine_list = medicine_list

        self.cabinet_state_pub.publish(msg)
        self.get_logger().debug(f"发布药柜状态: 药柜{msg.cabinet_id} 药品数量{len(msg.medicine_list)}")

    def publish_cabinet_running(self):
        """发布药柜运行状态"""
        msg = self.CabinetRunning()

        # 随机选择药柜ID (1-5)
        cabinet_id = random.randint(1, 5)
        isrunning = random.choice([0, 1])

        msg.cabinet_id = cabinet_id
        msg.isrunning = isrunning

        self.cabinet_running_pub.publish(msg)
        self.get_logger().debug(f"发布药柜运行状态: 药柜{cabinet_id} 运行状态{isrunning}")

    def publish_task_state(self):
        """发布任务状态"""
        msg = self.TaskState()

        # 模拟任务状态变化
        task_id = f"task_{self.task_counter}"
        self.task_counter += 1

        # 状态循环: 0->1->2->0...
        self.task_state = (self.task_state + 1) % 3
        car_id = random.randint(1, 3)

        msg.taskid = task_id
        msg.task_state = self.task_state
        msg.car_id = car_id

        self.task_state_pub.publish(msg)

        # 状态文本映射
        state_text = {0: "等待", 1: "执行中", 2: "完成"}.get(self.task_state, "未知")
        self.get_logger().debug(f"发布任务状态: 任务{task_id} 状态{state_text} 分配车辆{car_id}")

    def publish_task_data(self):
        """发布完整任务数据（模拟 Unity 的 TaskData_U）"""
        msg = self.Task()

        task_id = f"task_data_{self.task_counter}"
        msg.task_id = task_id
        msg.type = "0"

        cabinet = self.CabinetOrder()
        cabinet.cabinet_id = "cab_01"

        medicine = self.MedicineData()
        medicine.row = 1
        medicine.column = 2
        medicine.count = 3
        cabinet.medicine_list = [medicine]

        msg.cabinets = [cabinet]

        self.task_data_pub.publish(msg)
        self.get_logger().debug(f"发布任务数据: 任务ID={msg.task_id}, 类型={msg.type}")

def main(args=None):
    rclpy.init(args=args)

    try:
        node = SimulationPublisher()
        node.get_logger().info("仿真消息发布者启动成功")
        node.get_logger().info("按Ctrl+C停止节点")

        rclpy.spin(node)

    except KeyboardInterrupt:
        node.get_logger().info("节点被用户中断")
    except Exception as e:
        node.get_logger().error(f"节点运行错误: {e}")
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()