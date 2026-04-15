cmake_minimum_required(VERSION 3.8)
project(task_msgs)

# 查找必要的包
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 生成消息接口
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/MedicineData.msg"
  "msg/CabinetOrder.msg"
  "msg/Task.msg"
  "msg/CabinetRunning.msg"
  "msg/CabinetState.msg"
  "msg/CarState.msg"
  "msg/TaskState.msg"
)

# 导出运行时依赖
ament_export_dependencies(rosidl_default_runtime)

# 创建包（必须的最后一行）
ament_package()
