# 后端 - 智能取药系统

接收前端请求 → 校验药品 → 查坐标 → 写入取药记录 → 发布 ROS2 任务给算法控制小车。

## 快速开始

```bash

# 1. 初始化数据库
python3 init_db.py

# 2. 启动服务（若需 ROS2 下发任务，先 source /opt/ros/jazzy/setup.bash）
python3 app.py
```

服务运行在 `http://0.0.0.0:5000`

## API 说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查（含 ros2 是否连接） |
| GET | /api/drugs | 列出所有药品 |
| GET | /api/orders | 查看取药记录 |
| POST | /api/order | 批量取药（前端用） |
| POST | /api/pickup | 单条取药（兼容） |

### POST /api/order（批量）

**请求体**:
```json
[
  { "id": 1, "num": 2 },
  { "id": 2, "num": 1 }
]
```

**成功响应**:
```json
{
  "ok": true,
  "task_ids": [1, 2],
  "message": "已下发 2 个取药任务"
}
```

### ROS2 任务格式

任务发布到话题 `/task_request`，类型 `std_msgs/String`，JSON 内容：
```json
{
  "task_id": 1,
  "type": "pickup",
  "drug_id": 1,
  "name": "阿莫西林",
  "shelve_id": 1,
  "x": 1,
  "y": 1,
  "quantity": 2
}
```

**算法侧需订阅此话题**，解析后控制小车前往 `(x, y)` 取药。

## 前端对接

前端 `index.html` 请求 `http://localhost:5000/api/order`。若前后端不同机，修改 `index.html` 中 `API_BASE` 为后端地址。
