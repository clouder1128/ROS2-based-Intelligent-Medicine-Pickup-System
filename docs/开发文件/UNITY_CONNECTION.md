Unity 接入说明

概述
- 目标：使 Windows 上的 Unity 能通过 `ros_tcp_endpoint` 与本项目的 ROS2 后端以及前端正确通信。

当前可用的主机与端口（示例）
- Linux 主机 IP: 192.168.135.145
- ROS TCP Endpoint 端口: 11000  (如果需要可改为 10000)
- 后端（API）:  路径 http://192.168.135.145:8001
- 前端（静态）: http://192.168.135.145:8080

Unity 端设置（ROS TCP）
1. 在 Unity 中打开 RosConnection 或 ROS TCP 客户端配置。
2. 将 Host/IP 设置为 Linux 主机地址（例如：192.168.135.145）。
3. 将 Port 设置为 `11000`（或你在启动脚本中指定的 `ROS_TCP_PORT`）。
4. 启动 Unity 的 ROS 客户端。观察 Linux 端 `ros_tcp_endpoint` 日志，确认连接建立（会显示客户端已连接）。

在 Linux 主机上启动服务（示例）
- 使用 quick_start.sh 启动（在项目目录 `agent_with_backend`）：

```bash
# 使用已经验证可用的端口 11000
ROS_TCP_PORT=11000 ROS_DISTRO=jazzy bash quick_start.sh
```

- 若需使用默认 10000 端口，请先确保该端口未被系统占用（如 webmin）：

```bash
# 检查端口占用
ss -ltnp | grep 10000
# 若被 webmin 占用，可停止该服务（谨慎操作）
# sudo systemctl stop webmin
# 然后以 10000 启动
ROS_TCP_PORT=10000 ROS_DISTRO=jazzy bash quick_start.sh
```

防火墙与网络注意事项
- 确保 Linux 主机防火墙允许来自 Windows 的 TCP 连接到以下端口：
  - `11000`（或 `10000`）- ROS TCP
  - `8001` - 后端 API
  - `8080` - 前端静态服务器（如需远程访问）

常用防火墙命令示例：
- 使用 ufw：

```bash
sudo ufw allow 11000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 8080/tcp
```

- 使用 firewall-cmd（CentOS/RedHat）：

```bash
sudo firewall-cmd --add-port=11000/tcp --permanent
sudo firewall-cmd --add-port=8001/tcp --permanent
sudo firewall-cmd --reload
```

连接验证
- 在 Linux 上确认 ros_tcp_endpoint 正在监听：

```bash
ss -ltnp | grep 11000
```

- 在 Linux 或 Windows 上，通过浏览器或 curl 检查后端健康：

```bash
curl -s -o /dev/null -w "%{http_code}" http://192.168.135.145:8001/api/health
# 返回 200 则后端健康
```

- 在 ROS2 上（Linux）查看话题是否可见（Unity 客户端连接后）：

```bash
# 需要在已加载工作空间环境的 shell 中运行
ros2 topic list
```

常见问题与排查
- Unity 无法连接：
  - 检查 Linux 主机 IP 是否正确，Windows 是否能 ping 通。
  - 检查端口是否被防火墙或系统服务阻止。
  - 确认 `quick_start.sh` 中 `ROS_TCP_PORT` 与 Unity 配置一致。

- 后端 ROS 初始化失败（典型）：
  - 确保后端 venv 有必要的依赖（`PyYAML`, `numpy` 等），脚本 `quick_start.sh` 已做了处理。
  - 查看后端日志（在运行目录的终端或 `~/.ros/log/` 中的 launch 日志）。

变更记录
- 2026-05-21: 文档创建。当前项目在 `agent_with_backend` 中默认以 `ROS_TCP_PORT=11000` 启动以避免系统服务冲突。

