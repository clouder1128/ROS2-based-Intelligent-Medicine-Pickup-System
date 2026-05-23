#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from task_msgs.msg import CarState, CabinetState, CabinetRunning, TaskState, Task, MedicineData

class UnitySubscriber(Node):
    def __init__(self):
        super().__init__('unity_subscriber')
        
        # 创建四个订阅者
        self.car_state_subscriber = self.create_subscription(
            CarState,
            '/CarState_U',
            self.car_state_callback,
            10
        )
        
        self.cabinet_state_subscriber = self.create_subscription(
            CabinetState,
            '/CabinetState_U',
            self.cabinet_state_callback,
            10
        )
        
        self.cabinet_running_subscriber = self.create_subscription(
            CabinetRunning,
            '/CabinetRunning_U',
            self.cabinet_running_callback,
            10
        )
        
        self.task_state_subscriber = self.create_subscription(
            TaskState,
            '/TaskState_U',
            self.task_state_callback,
            10
        )

        self.task_data_subscriber = self.create_subscription(
            Task,
            '/TaskData_U',
            self.task_data_callback,
            10
        )
        
        self.get_logger().info('Unity消息接收器已启动...')

    def car_state_callback(self, msg):
        """处理CarState消息"""
        self.get_logger().info(
            f'收到CarState: 车辆ID={msg.car_id}, '
            f'位置({msg.x}, {msg.y}), '
            f'运行状态={msg.isrunning}'
        )

    def cabinet_state_callback(self, msg):
        """处理CabinetState消息"""
        self.get_logger().info(
            f'收到CabinetState: 药柜ID={msg.cabinet_id}, '
            f'药品数量={len(msg.medicine_list)}'
        )
        
        # 打印药品详情
        for i, medicine in enumerate(msg.medicine_list):
            self.get_logger().info(
                f'  药品{i+1}: 行={medicine.row}, '
                f'列={medicine.column}, '
                f'数量={medicine.count}'
            )

    def cabinet_running_callback(self, msg):
        """处理CabinetRunning消息"""
        self.get_logger().info(
            f'收到CabinetRunning: 药柜ID={msg.cabinet_id}, '
            f'运行状态={msg.isrunning}'
        )

    def task_state_callback(self, msg):
        """处理TaskState消息"""
        self.get_logger().info(
            f'收到TaskState: 任务ID={msg.taskid}, '
            f'任务状态={msg.task_state}, '
            f'分配车辆={msg.car_id}'
        )

    def task_data_callback(self, msg):
        """处理Task数据消息（来自 Unity TaskData_U）"""
        total_cabinets = len(msg.cabinets)
        total_medicines = sum(len(cab.medicine_list) for cab in msg.cabinets)
        self.get_logger().info(
            f'收到TaskData: 任务ID={msg.task_id}, '
            f'类型={msg.type}, '
            f'药柜数={total_cabinets}, 药品数={total_medicines}'
        )
        for i, cab in enumerate(msg.cabinets):
            for j, med in enumerate(cab.medicine_list):
                self.get_logger().info(
                    f'  药柜{cab.cabinet_id}: 行={med.row}, '
                    f'列={med.column}, 数量={med.count}'
                )

def main(args=None):
    rclpy.init(args=args)
    
    # 创建节点
    node = UnitySubscriber()
    
    try:
        # 保持节点运行
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # 清理资源
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
