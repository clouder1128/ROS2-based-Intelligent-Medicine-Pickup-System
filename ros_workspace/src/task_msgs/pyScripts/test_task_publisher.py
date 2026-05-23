#!/usr/bin/env python3
"""
通过setup.py安装的可运行节点 - 从JSON文件读取任务
"""

import rclpy
from rclpy.node import Node
from rclpy import qos
import json
import os

class TestTaskPublisher(Node):
    def __init__(self):
        super().__init__('test_task_publisher')
        
        try:
            from task_msgs.msg import Task, CabinetOrder, MedicineData
            self.Task = Task
            self.CabinetOrder = CabinetOrder
            self.MedicineData = MedicineData
        except ImportError as e:
            self.get_logger().error(f"导入失败: {e}")
            self.get_logger().info("请确保已正确构建和source工作空间")
            raise
        
        self.publisher = self.create_publisher(
            self.Task, 
            '/task_topic', 
            qos.qos_profile_system_default
        )
        
        # 定义JSON文件路径
        self.json_file_path = 'tasks.json'  # 默认当前目录
        
        # 检查JSON文件是否存在
        if not os.path.exists(self.json_file_path):
            self.get_logger().warning(f"JSON文件不存在: {self.json_file_path}")
            self.get_logger().info("将使用示例JSON文件格式创建tasks.json")
            self.create_example_json()
        
        # 读取JSON数据
        self.tasks_data = self.load_json_tasks()
        if not self.tasks_data:
            self.get_logger().error("没有可用的任务数据")
            return
            
        self.task_index = 0
        #self.timer = self.create_timer(2.0, self.publish_test_task)
        self.timer = self.create_timer(2.0, self.publish_test_task)
        self.get_logger().info(f'测试发布器已启动，从{self.json_file_path}读取任务数据')
    
    def load_json_tasks(self):
        """从JSON文件加载任务数据"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tasks = data.get('tasks', [])
                self.get_logger().info(f"成功加载JSON文件，找到{len(tasks)}个任务")
                return tasks
        except json.JSONDecodeError as e:
            self.get_logger().error(f"JSON解析失败: {e}")
        except Exception as e:
            self.get_logger().error(f"读取JSON文件失败: {e}")
        return []
    
    def create_example_json(self):
        """创建示例JSON文件（根据你提供的格式）"""
        example_data = {
            "tasks": [
                {
                    "task_id": "task_001",
                    "type": "0",
                    "cabinets": [
                        {
                            "cabinet_id": "cab_01",
                            "medicine_list": [
                                {"row": 1, "column": 2, "count": 3},
                                {"row": 3, "column": 4, "count": 2}
                            ]
                        },
                        {
                            "cabinet_id": "cab_02",
                            "medicine_list": [
                                {"row": 5, "column": 6, "count": 1}
                            ]
                        }
                    ]
                },
                {
                    "task_id": "task_002",
                    "type": "1",
                    "cabinets": [
                        {
                            "cabinet_id": "cab_03",
                            "medicine_list": [
                                {"row": 2, "column": 3, "count": 5},
                                {"row": 4, "column": 5, "count": 3},
                                {"row": 6, "column": 7, "count": 2}
                            ]
                        }
                    ]
                },
                {
                    "task_id": "task_003",
                    "type": "0",
                    "cabinets": [
                        {
                            "cabinet_id": "cab_01",
                            "medicine_list": [
                                {"row": 7, "column": 8, "count": 4}
                            ]
                        },
                        {
                            "cabinet_id": "cab_03",
                            "medicine_list": [
                                {"row": 1, "column": 1, "count": 1}
                            ]
                        },
                        {
                            "cabinet_id": "cab_05",
                            "medicine_list": [
                                {"row": 9, "column": 10, "count": 2}
                            ]
                        }
                    ]
                }
            ]
        }
        
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(example_data, f, indent=2, ensure_ascii=False)
            self.get_logger().info(f"已创建示例JSON文件: {self.json_file_path}")
        except Exception as e:
            self.get_logger().error(f"创建示例JSON文件失败: {e}")
    
    def publish_test_task(self):
        """从JSON文件读取并发布任务"""
        try:
            # tasks_data现在直接是任务列表
            if not self.tasks_data:
                self.get_logger().warning("JSON文件中没有任务数据")
                return
            
            # 循环发送任务
            if self.task_index >= len(self.tasks_data):
                self.task_index = 0  # 重新开始循环
                self.get_logger().info("所有任务已发送一遍")
            
            task_info = self.tasks_data[self.task_index]
            
            # 创建Task消息
            task_msg = self.Task()
            task_msg.task_id = str(task_info.get('task_id', f'unknown_{self.task_index}'))
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
            
            # 发布消息
            self.publisher.publish(task_msg)
            
            # 统计药品总数
            total_medicines = sum(len(cab.medicine_list) for cab in cabinets)
            self.get_logger().info(
                f'已发布任务 {self.task_index + 1}/{len(self.tasks_data)}: '
                f'任务ID={task_msg.task_id}, '
                f'类型={task_msg.type}, '
                f'药柜数={len(cabinets)}, '
                f'药品数={total_medicines}'
            )
            
            # 打印详细药品信息
            for i, cab in enumerate(cabinets):
                for j, med in enumerate(cab.medicine_list):
                    self.get_logger().info(
                        f'  药柜{cab.cabinet_id}: 第{j+1}个药品 - '
                        f'行={med.row}, 列={med.column}, 数量={med.count}'
                    )
            
            # 移动到下一个任务
            self.task_index += 1
            
        except KeyError as e:
            self.get_logger().error(f"JSON数据格式错误，缺少字段: {e}")
        except ValueError as e:
            self.get_logger().error(f"数据类型转换错误: {e}")
        except Exception as e:
            self.get_logger().error(f'发布任务时出错: {e}')

def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = TestTaskPublisher()
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
