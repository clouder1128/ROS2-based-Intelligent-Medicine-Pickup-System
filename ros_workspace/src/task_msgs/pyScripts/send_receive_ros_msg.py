#!/usr/bin/env python3
"""
处方任务发送与仿真消息接收节点
功能：
1. 根据处方信息生成任务并发送到仿真端
2. 接收仿真端发布的所有消息（车辆状态、药柜状态、药柜运行状态、任务状态）
"""

import rclpy
from rclpy.node import Node
from rclpy import qos
import json
import os
import time

class PrescriptionSenderReceiver(Node):
    def __init__(self, prescription_file=None):
        """
        初始化处方发送与消息接收节点

        Args:
            prescription_file: 处方信息JSON文件路径（可选）
        """
        super().__init__('prescription_sender_receiver')

        # 初始化消息类型
        self.init_message_types()

        # 设置处方文件路径
        if prescription_file and os.path.exists(prescription_file):
            self.prescription_file = prescription_file
        else:
            self.prescription_file = 'prescriptions.json'
            if not os.path.exists(self.prescription_file):
                self.create_example_prescription_file()

        # 加载处方数据
        self.prescriptions = self.load_prescriptions()
        self.current_prescription_index = 0

        # 创建任务发布者
        self.task_publisher = self.create_publisher(
            self.Task,
            '/task_topic',
            qos.qos_profile_system_default
        )

        # 创建仿真消息订阅者
        self.init_simulation_subscribers()

        # 定时器：每5秒发送一个处方任务
        self.send_timer = self.create_timer(5.0, self.send_prescription_task)

        # 状态跟踪
        self.sent_count = 0
        self.received_messages = {
            'CarState': 0,
            'CabinetState': 0,
            'CabinetRunning': 0,
            'TaskState': 0,
            'TaskData': 0
        }

        self.get_logger().info('处方任务发送与仿真消息接收节点已启动')
        self.get_logger().info(f'已加载 {len(self.prescriptions)} 个处方')
        self.log_subscription_status()

    def init_message_types(self):
        """初始化所有需要的消息类型"""
        try:
            # 导入发送任务所需的消息类型
            from task_msgs.msg import Task, CabinetOrder, MedicineData
            self.Task = Task
            self.CabinetOrder = CabinetOrder
            self.MedicineData = MedicineData

            # 导入接收仿真消息所需的消息类型
            from task_msgs.msg import CarState, CabinetState, CabinetRunning, TaskState
            self.CarState = CarState
            self.CabinetState = CabinetState
            self.CabinetRunning = CabinetRunning
            self.TaskState = TaskState

        except ImportError as e:
            self.get_logger().error(f"消息类型导入失败: {e}")
            self.get_logger().info("请确保已正确构建和source工作空间")
            raise

    def init_simulation_subscribers(self):
        """初始化所有仿真消息订阅者"""
        # 订阅车辆状态
        self.car_state_sub = self.create_subscription(
            self.CarState,
            '/CarState_U',
            self.car_state_callback,
            qos.qos_profile_sensor_data
        )

        # 订阅药柜状态
        self.cabinet_state_sub = self.create_subscription(
            self.CabinetState,
            '/CabinetState_U',
            self.cabinet_state_callback,
            qos.qos_profile_sensor_data
        )

        # 订阅药柜运行状态
        self.cabinet_running_sub = self.create_subscription(
            self.CabinetRunning,
            '/CabinetRunning_U',
            self.cabinet_running_callback,
            qos.qos_profile_sensor_data
        )

        # 订阅任务状态
        self.task_state_sub = self.create_subscription(
            self.TaskState,
            '/TaskState_U',
            self.task_state_callback,
            qos.qos_profile_sensor_data
        )

        # 订阅完整任务数据（来自 Unity TaskData_U）
        self.task_data_sub = self.create_subscription(
            self.Task,
            '/TaskData_U',
            self.task_data_callback,
            qos.qos_profile_sensor_data
        )

    def log_subscription_status(self):
        """记录订阅状态"""
        self.get_logger().info('已订阅以下仿真主题：')
        self.get_logger().info('  - /CarState_U (车辆状态)')
        self.get_logger().info('  - /CabinetState_U (药柜状态)')
        self.get_logger().info('  - /CabinetRunning_U (药柜运行状态)')
        self.get_logger().info('  - /TaskState_U (任务状态)')
        self.get_logger().info('  - /TaskData_U (完整任务数据)')

    def load_prescriptions(self):
        """
        从JSON文件加载处方信息

        Returns:
            list: 处方数据列表
        """
        try:
            with open(self.prescription_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                prescriptions = data.get('prescriptions', [])
                self.get_logger().info(f"成功加载处方文件，找到 {len(prescriptions)} 个处方")
                return prescriptions
        except json.JSONDecodeError as e:
            self.get_logger().error(f"处方JSON解析失败: {e}")
        except Exception as e:
            self.get_logger().error(f"读取处方文件失败: {e}")
        return []

    def create_example_prescription_file(self):
        """创建示例处方文件"""
        example_data = {
            "prescriptions": [
                {
                    "prescription_id": "RX2026001",
                    "patient_id": "P001",
                    "patient_name": "张三",
                    "diagnosis": "高血压",
                    "date": "2026-04-04",
                    "task": {
                        "task_id": "task_from_RX2026001",
                        "type": "0",
                        "cabinets": [
                            {
                                "cabinet_id": "cab_01",
                                "medicine_list": [
                                    {"row": 1, "column": 2, "count": 3, "medicine_name": "降压药A"},
                                    {"row": 3, "column": 4, "count": 2, "medicine_name": "降压药B"}
                                ]
                            }
                        ]
                    }
                },
                {
                    "prescription_id": "RX2026002",
                    "patient_id": "P002",
                    "patient_name": "李四",
                    "diagnosis": "糖尿病",
                    "date": "2026-04-04",
                    "task": {
                        "task_id": "task_from_RX2026002",
                        "type": "1",
                        "cabinets": [
                            {
                                "cabinet_id": "cab_02",
                                "medicine_list": [
                                    {"row": 5, "column": 6, "count": 1, "medicine_name": "降糖药A"},
                                    {"row": 7, "column": 8, "count": 2, "medicine_name": "降糖药B"},
                                    {"row": 9, "column": 10, "count": 1, "medicine_name": "胰岛素"}
                                ]
                            }
                        ]
                    }
                },
                {
                    "prescription_id": "RX2026003",
                    "patient_id": "P003",
                    "patient_name": "王五",
                    "diagnosis": "感冒",
                    "date": "2026-04-04",
                    "task": {
                        "task_id": "task_from_RX2026003",
                        "type": "0",
                        "cabinets": [
                            {
                                "cabinet_id": "cab_03",
                                "medicine_list": [
                                    {"row": 2, "column": 3, "count": 5, "medicine_name": "感冒药A"}
                                ]
                            },
                            {
                                "cabinet_id": "cab_04",
                                "medicine_list": [
                                    {"row": 4, "column": 5, "count": 3, "medicine_name": "感冒药B"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }

        try:
            with open(self.prescription_file, 'w', encoding='utf-8') as f:
                json.dump(example_data, f, indent=2, ensure_ascii=False)
            self.get_logger().info(f"已创建示例处方文件: {self.prescription_file}")
        except Exception as e:
            self.get_logger().error(f"创建示例处方文件失败: {e}")

    def generate_task_from_prescription(self, prescription_data):
        """
        根据处方数据生成ROS任务消息

        Args:
            prescription_data: 处方数据字典

        Returns:
            Task: 生成的ROS任务消息
        """
        task_info = prescription_data.get('task', {})

        # 创建Task消息
        task_msg = self.Task()
        task_msg.task_id = str(task_info.get('task_id', f'unknown_{self.current_prescription_index}'))
        task_msg.type = str(task_info.get('type', '0'))

        # 创建CabinetOrder列表
        cabinets = []
        for cab_info in task_info.get('cabinets', []):
            cabinet = self.CabinetOrder()
            cabinet.cabinet_id = str(cab_info.get('cabinet_id', ''))

            # 创建MedicineData列表
            medicine_list = []
            for med_info in cab_info.get('medicine_list', []):
                medicine = self.MedicineData()
                medicine.row = int(med_info.get('row', 0))
                medicine.column = int(med_info.get('column', 0))
                medicine.count = int(med_info.get('count', 0))
                medicine_list.append(medicine)

            cabinet.medicine_list = medicine_list
            cabinets.append(cabinet)

        task_msg.cabinets = cabinets

        return task_msg

    def send_prescription_task(self):
        """定时器回调：发送处方任务"""
        if not self.prescriptions:
            self.get_logger().warning("没有可用的处方数据")
            return

        # 循环发送处方
        if self.current_prescription_index >= len(self.prescriptions):
            self.current_prescription_index = 0
            self.get_logger().info("所有处方已发送一遍，重新开始循环")

        prescription = self.prescriptions[self.current_prescription_index]

        try:
            # 生成任务消息
            task_msg = self.generate_task_from_prescription(prescription)

            # 发布任务
            self.task_publisher.publish(task_msg)

            # 更新统计
            self.sent_count += 1

            # 计算统计信息
            total_cabinets = len(task_msg.cabinets)
            total_medicines = sum(len(cab.medicine_list) for cab in task_msg.cabinets)

            # 记录发送信息
            self.get_logger().info("=" * 60)
            self.get_logger().info(f"处方 {self.current_prescription_index + 1}/{len(self.prescriptions)} 已发送")
            self.get_logger().info(f"处方ID: {prescription.get('prescription_id', '未知')}")
            self.get_logger().info(f"患者: {prescription.get('patient_name', '未知')} ({prescription.get('patient_id', '未知')})")
            self.get_logger().info(f"诊断: {prescription.get('diagnosis', '未知')}")
            self.get_logger().info(f"任务ID: {task_msg.task_id}, 类型: {task_msg.type}")
            self.get_logger().info(f"药柜数: {total_cabinets}, 药品数: {total_medicines}")

            # 打印药品详情
            for i, cab in enumerate(task_msg.cabinets):
                self.get_logger().info(f"  药柜 {i+1}: {cab.cabinet_id} ({len(cab.medicine_list)}个药品)")
                for j, med in enumerate(cab.medicine_list):
                    self.get_logger().info(f"    药品 {j+1}: 行={med.row}, 列={med.column}, 数量={med.count}")

            self.get_logger().info(f"累计发送任务数: {self.sent_count}")
            self.get_logger().info("=" * 60)

            # 移动到下一个处方
            self.current_prescription_index += 1

        except KeyError as e:
            self.get_logger().error(f"处方数据格式错误，缺少字段: {e}")
        except ValueError as e:
            self.get_logger().error(f"数据类型转换错误: {e}")
        except Exception as e:
            self.get_logger().error(f"发送处方任务时出错: {e}")

    def car_state_callback(self, msg):
        """车辆状态回调函数"""
        self.received_messages['CarState'] += 1
        self.get_logger().info(f"[车辆状态] 车辆ID={msg.car_id}, 位置({msg.x:.2f}, {msg.y:.2f}), 运行状态={msg.isrunning}")

    def cabinet_state_callback(self, msg):
        """药柜状态回调函数"""
        self.received_messages['CabinetState'] += 1
        self.get_logger().info(f"[药柜状态] 药柜ID={msg.cabinet_id}, 药品数量={len(msg.medicine_list)}")

        # 打印药品详情（前3个）
        for i, medicine in enumerate(msg.medicine_list[:3]):
            self.get_logger().info(f"  药品{i+1}: 行={medicine.row}, 列={medicine.column}, 数量={medicine.count}")

        if len(msg.medicine_list) > 3:
            self.get_logger().info(f"  ... 还有{len(msg.medicine_list) - 3}个药品")

    def cabinet_running_callback(self, msg):
        """药柜运行状态回调函数"""
        self.received_messages['CabinetRunning'] += 1
        status = "运行中" if msg.isrunning else "停止"
        self.get_logger().info(f"[药柜运行] 药柜ID={msg.cabinet_id}, 状态={status}")

    def task_state_callback(self, msg):
        """任务状态回调函数"""
        self.received_messages['TaskState'] += 1

        # 任务状态映射
        state_mapping = {
            0: "等待",
            1: "执行中",
            2: "完成",
            3: "失败",
            -1: "未知"
        }

        state_text = state_mapping.get(msg.task_state, f"未知({msg.task_state})")
        self.get_logger().info(f"[任务状态] 任务ID={msg.taskid}, 状态={state_text}, 分配车辆={msg.car_id}")

    def task_data_callback(self, msg):
        """完整任务数据回调函数（接收 Unity TaskData_U 的 Task 消息）"""
        self.received_messages['TaskData'] += 1
        total_cabinets = len(msg.cabinets)
        total_medicines = sum(len(cab.medicine_list) for cab in msg.cabinets)
        self.get_logger().info(f"[任务数据] 任务ID={msg.task_id}, 类型={msg.type}, "
                               f"药柜数={total_cabinets}, 药品数={total_medicines}")
        for i, cab in enumerate(msg.cabinets):
            for j, med in enumerate(cab.medicine_list):
                self.get_logger().info(f"  药柜{cab.cabinet_id}: 行={med.row}, 列={med.column}, 数量={med.count}")

    def print_statistics(self):
        """打印消息统计信息"""
        self.get_logger().info("=" * 60)
        self.get_logger().info("消息统计:")
        self.get_logger().info(f"  已发送任务数: {self.sent_count}")
        self.get_logger().info(f"  接收到的车辆状态消息: {self.received_messages['CarState']}")
        self.get_logger().info(f"  接收到的药柜状态消息: {self.received_messages['CabinetState']}")
        self.get_logger().info(f"  接收到的药柜运行消息: {self.received_messages['CabinetRunning']}")
        self.get_logger().info(f"  接收到的任务状态消息: {self.received_messages['TaskState']}")
        self.get_logger().info(f"  接收到的任务数据消息: {self.received_messages['TaskData']}")
        total_received = sum(self.received_messages.values())
        self.get_logger().info(f"  总计接收消息数: {total_received}")
        self.get_logger().info("=" * 60)

def main(args=None):
    rclpy.init(args=args)

    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='处方任务发送与仿真消息接收节点')
    parser.add_argument('--prescription-file', '-f', type=str,
                       help='处方信息JSON文件路径', default=None)
    parser.add_argument('--send-interval', '-i', type=float,
                       help='任务发送间隔（秒）', default=5.0)

    # 注意：rclpy有自己的参数解析，需要特殊处理
    # 这里简化处理，假设参数在--ros-args之后
    try:
        node = PrescriptionSenderReceiver()

        # 可以调整定时器间隔
        if '--send-interval' in str(args) or '-i' in str(args):
            # 简化处理，实际应用中需要更复杂的参数解析
            node.get_logger().info("使用默认发送间隔5.0秒")

        node.get_logger().info("节点启动成功，开始运行...")
        node.get_logger().info("按Ctrl+C停止节点")

        # 设置定时打印统计信息
        stats_timer = node.create_timer(30.0, node.print_statistics)

        rclpy.spin(node)

    except KeyboardInterrupt:
        node.get_logger().info("节点被用户中断")
        node.print_statistics()
    except Exception as e:
        node.get_logger().error(f"节点运行错误: {e}")
    finally:
        if 'node' in locals():
            try:
                node.destroy_node()
            except Exception as e:
                node.get_logger().error(f"销毁节点时出错: {e}")
        try:
            rclpy.shutdown()
        except Exception as e:
            # 忽略shutdown时的错误，因为上下文可能已经无效
            pass

if __name__ == '__main__':
    main()