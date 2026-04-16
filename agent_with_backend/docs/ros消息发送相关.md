# 审批确认后流程分析与ROS消息查看指南

## 概述

本文档详细描述了在ROS2-based-Intelligent-Medicine-Pickup-System中，医生确认审批后发生的完整流程，以及如何查看在ROS话题上发布的消息。

## 1. 审批确认后的完整流程

### 1.1 命令行操作流程

1. **患者开药**：
   ```bash
   make patient
   ```
   - 启动患者CLI，创建审批请求

2. **医生确认审批**：
   ```bash
   make doctor
   ```
   - 启动医生CLI，查看并确认待审批的申请单

### 1.2 API调用路径

```
医生CLI → POST /api/approvals/{approval_id}/approve → approval_controller.approve_approval()
```

### 1.3 核心处理流程

源代码位置：[approval_controller.py:196-306](agent_with_backend/backend/controllers/approval_controller.py#L196-L306)

```python
# 关键处理步骤：
1. manager.approve(approval_id, doctor_id)        # 更新审批状态为"approved"
2. find_drug_id_by_name(drug_name)               # 根据药品名称查找药品ID
3. validate_and_get_drug(drug_id, quantity)       # 验证药品和库存可用性
4. 数据库事务处理：
   - UPDATE inventory SET quantity = quantity - ?  # 扣减库存
   - INSERT INTO order_log (...)                   # 创建订单记录
   - 获取 task_id = cur.lastrowid
5. publish_task(task_id, drug, quantity)           # 发布ROS2取药任务
```

### 1.4 ROS2消息发布链

```
publish_task() → ros2_bridge.publish_task() → TaskPublisher.publish_task()
```

#### 发布模式配置
源代码位置：[config.py:14-15](agent_with_backend/backend/ros_integration/config.py#L14-L15)

系统支持三种集成模式，通过环境变量 `ROS_INTEGRATION_MODE` 控制：

| 模式 | 描述 | 发布话题 |
|------|------|----------|
| `new` | 仅使用新话题格式 | `/task_topic` |
| `legacy` | 仅使用旧话题格式 | `/task_request` |
| `parallel` | 新旧话题同时发布 | `/task_topic` 和 `/task_request` |

#### 话题名称
源代码位置：[config.py:27-28](agent_with_backend/backend/ros_integration/config.py#L27-L28)

- `/task_topic` - 新话题（使用结构化 `task_msgs.msg.Task` 消息格式）
- `/task_request` - 旧话题（使用 `std_msgs.msg.String` JSON字符串格式）

### 1.5 消息格式转换

`MessageAdapter.backend_to_unity()` 负责格式转换：
源代码位置：[message_adapter.py:32-94](agent_with_backend/backend/ros_integration/message_adapter.py#L32-L94)

```python
# Backend药品数据格式
{
    "drug_id": 1,
    "name": "布洛芬",
    "shelve_id": "A",
    "shelf_x": 3,      # 列坐标
    "shelf_y": 4,      # 行坐标
    "quantity": 2      # 库存数量
}

# 转换为Unity Task消息格式
Task消息:
- task_id: "12345"              # 任务ID
- type: "0"                     # 任务类型："0"表示取药
- cabinets[0].cabinet_id: "A"   # 货架ID
- cabinets[0].medicine_list[0]:
  - column: 3                   # 列坐标（映射自shelf_x）
  - row: 4                      # 行坐标（映射自shelf_y）
  - count: 2                    # 取药数量
```

**重要映射关系**：
- `shelf_x` → `column`（列坐标）
- `shelf_y` → `row`（行坐标）
- `shelve_id` → `cabinet_id`（货架ID）

## 2. 如何查看ROS话题上发布的消息

### 2.1 环境准备

确保已激活ROS2环境：
```bash
source /opt/ros/jazzy/setup.bash
```

### 2.2 基础查看命令

#### 查看所有活跃话题：
```bash
ros2 topic list
```
预期输出包含：
```
/task_topic
/task_request
/TaskState_U
/CarState_U
/CabinetState_U
```

#### 实时查看消息内容：

**新话题消息**（结构化格式）：
```bash
ros2 topic echo /task_topic
```
输出示例：
```
task_id: '1001'
type: '0'
cabinets:
- cabinet_id: 'A'
  medicine_list:
  - column: 3
    row: 4
    count: 2
---
```

**旧话题消息**（JSON格式）：
```bash
ros2 topic echo /task_request
```
输出示例：
```
data: '{"task_id": 1001, "type": "pickup", "drug_id": 1, "name": "布洛芬", "shelve_id": "A", "x": 3, "y": 4, "quantity": 2}'
---
```

### 2.3 高级监控命令

#### 查看话题详细信息：
```bash
# 查看话题类型和发布/订阅者数量
ros2 topic info /task_topic
```
输出：
```
Type: task_msgs/msg/Task
Publisher count: 1
Subscription count: 0
```

#### 监控消息发布频率：
```bash
ros2 topic hz /task_topic
```
输出：
```
average rate: 0.500
	min: 2.000s max: 2.000s std dev: 0.00000s window: 2
```

#### 查看消息类型定义：
```bash
ros2 interface show task_msgs/msg/Task
```

#### 一次性查看消息（不持续监听）：
```bash
ros2 topic echo /task_topic --once
```

#### 查看特定话题的历史消息：
```bash
ros2 topic echo /task_topic --qos-history-depth 10
```

### 2.4 集成测试中的查看方法

参考项目中的ROS集成测试文档：
- [ROS集成测试说明](agent_with_backend/docs/ros集成测试说明.md)

测试阶段的关键监控命令：
```bash
# 阶段3：端到端测试中的监控命令
ros2 topic list
ros2 topic echo /task_topic
ros2 topic echo /task_request
ros2 topic echo /TaskState_U
ros2 topic echo /CarState_U
ros2 topic echo /CabinetState_U
```

### 2.5 调试技巧

#### 1. 确保task_msgs包可用
```bash
# 构建task_msgs包
cd /home/clouder/ROS2-based-Intelligent-Medicine-Pickup-System/ros-todo/ros_workspace
colcon build --packages-select task_msgs
source install/setup.bash

# 验证Python导入
python3 -c "from task_msgs.msg import Task; print('Task消息导入成功')"
```

#### 2. 检查ROS2节点状态
```bash
# 查看所有运行中的节点
ros2 node list

# 查看特定节点信息
ros2 node info /backend_ros_integration
```

#### 3. 查看系统日志
后端应用会输出详细的ROS2集成日志，可在控制台或日志文件中查看：
```bash
# 查看后端日志输出
tail -f backend.log  # 或直接查看控制台输出
```

日志示例：
```
[TaskPublisher] Published task 1001 to /task_topic
[ROS2 Bridge] Published task task_id=1001 -> (3,4)
[TaskPublisher] Also published task 1001 to /task_request
```

#### 4. 使用rviz2可视化（如已配置）
```bash
rviz2
```

## 3. 完整验证流程示例

```bash
# 终端1：启动后端服务
cd /home/clouder/ROS2-based-Intelligent-Medicine-Pickup-System/agent_with_backend
make backend-start

# 终端2：激活ROS环境并监控话题
source /opt/ros/jazzy/setup.bash
ros2 topic echo /task_topic

# 终端3：执行患者开药流程
make patient
# 按照提示创建审批请求

# 终端4：执行医生审批流程
make doctor
# 按照提示查看并确认审批

# 观察终端2中的消息输出
```

## 4. 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 看不到任何ROS话题 | ROS2环境未激活 | 执行 `source /opt/ros/jazzy/setup.bash` |
| 话题存在但无消息发布 | 集成模式配置不匹配 | 检查 `ROS_INTEGRATION_MODE` 环境变量 |
| 导入task_msgs失败 | 包未安装或Python路径错误 | 重新构建包并正确设置PYTHONPATH |
| 消息格式错误或坐标异常 | 行列映射问题 | 检查 `shelf_x`→`column`、`shelf_y`→`row` 映射 |
| 消息发布但Unity未接收 | 话题名称不匹配 | 确认Unity订阅的话题名称与后端发布一致 |
| 数据库操作成功但无ROS消息 | ROS2节点初始化失败 | 检查后端日志中的ROS2初始化错误 |

### 4.1 环境变量配置

关键环境变量：
```bash
# 集成模式控制
export ROS_INTEGRATION_MODE="parallel"  # new, legacy, parallel

# ROS2域ID（避免冲突）
export ROS_DOMAIN_ID="42"

# ROS TCP连接配置
export ROS_TCP_ENABLED="True"
export ROS_IP="0.0.0.0"
export ROS_TCP_PORT="10000"

# task_msgs Python路径
export PYTHONPATH="/home/clouder/ROS2-based-Intelligent-Medicine-Pickup-System/ros-todo/ros_workspace/install/task_msgs/lib/python3.12/site-packages:$PYTHONPATH"
```

### 4.2 日志级别调整

如需更详细的调试信息，可调整日志级别：
```python
# 在backend/main.py中调整
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 5. 相关源代码文件

1. **审批控制器**：`agent_with_backend/backend/controllers/approval_controller.py`
2. **订单控制器**：`agent_with_backend/backend/controllers/order_controller.py`
3. **ROS2桥接器**：`agent_with_backend/backend/utils/ros2_bridge.py`
4. **任务发布器**：`agent_with_backend/backend/ros_integration/task_publisher.py`
5. **消息适配器**：`agent_with_backend/backend/ros_integration/message_adapter.py`
6. **配置管理**：`agent_with_backend/backend/ros_integration/config.py`
7. **主应用**：`agent_with_backend/backend/main.py`

## 6. 参考资料

1. [ROS2官方文档](https://docs.ros.org/)
2. [项目ROS集成测试说明](agent_with_backend/docs/ros集成测试说明.md)
3. [项目架构文档](agent_with_backend/docs/agent_with_backend_architecture.md)

---

**最后更新**：2026-04-15  
**文档版本**：1.0  
**维护者**：Claude Code Assistant