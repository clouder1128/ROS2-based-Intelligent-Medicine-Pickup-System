# 快速开始指南

本文档提供ROS2智能取药系统仿真项目的快速启动步骤，帮助用户在最短时间内搭建和运行系统。

## 系统要求

### 硬件要求
- **Windows PC**：运行Unity仿真程序（建议8GB+ RAM，独立显卡）
- **Linux PC/虚拟机**：运行ROS2系统（建议4GB+ RAM）
- **网络**：两台机器需在同一局域网内

### 软件要求
- **Windows端**：
  - Windows 10/11
  - Unity可执行程序（已包含在项目中）
  - 文本编辑器（配置ip.txt）

- **Linux端**：
  - Ubuntu 22.04 LTS（推荐）
  - ROS2 Humble Hawksbill
  - Python 3.8+
  - Git

## 环境准备

### 1. Linux端（ROS2）环境搭建

#### 安装ROS2 Humble
```bash
# 设置locale
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 添加ROS2仓库
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 安装ROS2
sudo apt update
sudo apt install ros-humble-desktop
sudo apt install python3-colcon-common-extensions

# 配置环境变量
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

#### 获取项目代码
```bash
# 克隆项目（或从本地上传）
cd ~
git clone <项目仓库URL>
cd ROS2-based-Intelligent-Medicine-Pickup-System
```

### 2. Windows端环境准备

#### 获取Unity可执行程序
1. 下载或从项目中获取 `unity_simulation/RosCar` 目录
2. 确保目录完整，包含所有必要的DLL和资源文件

#### 配置网络连接
1. 进入 `RosCar/ROSPackage_Data/StreamingAssets/` 目录
2. 编辑 `ip.txt` 文件，填入Linux端的IP地址：
   ```
   192.168.x.x  # 替换为实际的ROS2服务器IP
   ```

## 系统启动步骤

### 步骤1：启动ROS2服务器（Linux端）

```bash
# 1. 进入ROS工作空间
cd ~/ROS2-based-Intelligent-Medicine-Pickup-System/ros_workspace

# 2. 设置ROS2环境
source /opt/ros/humble/setup.bash
source install/setup.bash

# 3. 启动ROS-TCP-Endpoint服务器
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args \
  -p ROS_IP:=0.0.0.0 \
  -p ROS_TCP_PORT:=10000
```

**预期输出**：
```
[INFO] [ros_tcp_endpoint]: TCP endpoint started on 0.0.0.0:10000
```

### 步骤2：启动任务发布器（可选，Linux端）

```bash
# 1. 新开终端，进入ROS工作空间
cd ~/ROS2-based-Intelligent-Medicine-Pickup-System/ros_workspace
source install/setup.bash

# 2. 运行测试任务发布器
cd src/task_msgs/pyScripts
python3 test_task_publisher.py
```

**预期输出**：
```
[INFO] [test_task_publisher]: 测试发布器已启动，从tasks.json读取任务数据
[INFO] [test_task_publisher]: 已发布任务 1/3: 任务ID=task_001, 类型=0, 药柜数=2, 药品数=5
```

### 步骤3：启动Unity仿真（Windows端）

1. **运行可执行程序**：
   - 进入 `unity_simulation/RosCar` 目录
   - 双击 `ROSPackage.exe`（或相应的可执行文件）

2. **系统初始化**：
   - Unity程序启动后，自动读取 `ip.txt` 配置
   - 连接ROS2服务器（状态显示在控制台）

3. **用户界面操作**：
   - 按 **F1** 键显示/隐藏主控制面板
   - 在任务面板中查看从ROS2接收的任务
   - 点击任务按钮分配车辆执行

### 步骤4：监控系统状态（Linux端）

```bash
# 在新终端中监控各个Topic
cd ~/ROS2-based-Intelligent-Medicine-Pickup-System/ros_workspace
source install/setup.bash

# 查看所有活跃的Topic
ros2 topic list

# 实时监控关键Topic
ros2 topic echo /CabinetRunning_U --full
ros2 topic echo /CabinetState_U --full
ros2 topic echo /CarState_U --full
ros2 topic echo /TaskData_U --full
```

## 测试验证流程

### 基本功能测试

1. **网络连接测试**：
   ```bash
   # 在Windows端测试连接
   ping <Linux_IP>
   
   # 在Linux端检查端口
   sudo netstat -tlnp | grep 10000
   ```

2. **ROS通信测试**：
   - 确认Unity控制台显示"Connected to ROS"
   - 确认ROS2端显示新的客户端连接

3. **任务流程测试**：
   - 在ROS2端发布测试任务
   - 在Unity界面查看任务列表
   - 分配车辆执行任务
   - 观察车辆移动和药柜操作动画

### 完整工作流测试

```
1. ROS2发布任务 → 2. Unity接收任务 → 3. 用户分配车辆 → 
4. 车辆前往药柜 → 5. 药柜执行取药 → 6. 车辆前往目的地 → 
7. 完成交付 → 8. 状态反馈ROS2
```

## 故障排除

### 常见问题及解决方案

#### 问题1：Unity无法连接ROS2服务器
**症状**：Unity控制台显示连接失败或超时
**解决方案**：
1. 检查 `ip.txt` 中的IP地址是否正确
2. 确保Linux防火墙允许10000端口
   ```bash
   sudo ufw allow 10000/tcp
   ```
3. 检查网络连通性
   ```bash
   # 在Windows端
   telnet <Linux_IP> 10000
   ```

#### 问题2：ROS2 Topic无法接收消息
**症状**：`ros2 topic echo` 没有输出
**解决方案**：
1. 确认Unity已正确发布消息
2. 检查Topic名称是否匹配
3. 确认消息类型一致
   ```bash
   ros2 topic info /CarState_U
   ros2 interface show task_msgs/msg/CarState
   ```

#### 问题3：车辆不执行任务
**症状**：任务已分配但车辆不动
**解决方案**：
1. 检查车辆状态是否正常
2. 确认轨迹文件是否存在
3. 查看Unity控制台错误日志

#### 问题4：药柜动画异常
**症状**：药柜机械臂不动或位置错误
**解决方案**：
1. 检查药柜ID配置
2. 确认药品行列值在有效范围内（行1-9，列1-5）
3. 查看药品库存数据

## 高级配置

### 自定义任务数据

编辑 `configs/tasks.json` 文件，自定义任务配置：
```json
{
  "tasks": [
    {
      "task_id": "custom_task_001",
      "type": "0",
      "cabinets": [
        {
          "cabinet_id": "cab_01",
          "medicine_list": [
            {"row": 1, "column": 1, "count": 3},
            {"row": 2, "column": 3, "count": 2}
          ]
        }
      ]
    }
  ]
}
```

### 调整仿真参数

在Unity编辑器中调整：
1. **车辆参数**：速度、加速度、转向灵敏度
2. **药柜参数**：机械臂速度、药品矩阵大小
3. **通信参数**：发布频率、超时时间

### 性能优化

1. **降低渲染质量**：提高帧率
2. **减少传感器数据频率**：降低网络负载
3. **使用静态障碍物**：减少物理计算

## 下一步

成功运行基础系统后，可以尝试：

1. **扩展功能**：添加新的传感器或执行器
2. **集成真实硬件**：连接真实AGV或机械臂
3. **算法开发**：实现智能调度算法
4. **多机协作**：扩展为多车多柜系统

## 获取帮助

- **查看详细文档**：`docs/` 目录下的API接口和设计文档
- **检查日志文件**：Unity和ROS2的日志文件
- **提交Issue**：在项目仓库中报告问题

---
*文档更新时间：2026-04-07*