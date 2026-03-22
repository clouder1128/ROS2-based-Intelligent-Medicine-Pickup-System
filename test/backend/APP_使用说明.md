# app.py 使用说明

> app.py 是智能取药系统的**中枢**：接收前端药单、查库定位、生成取药记录、向 ROS2 下发任务，供算法控制小车执行。

---

## 一、整体架构（三者关系）

```
┌─────────────────┐         HTTP/JSON          ┌─────────────────┐
│   前端 index.html │  ◄────────────────────────►  │   app.py 后端   │
│  (用户输入药单)   │      POST /api/order       │  (Flask + DB)   │
└─────────────────┘                              └────────┬────────┘
                                                          │
                                                          │ ROS2 话题
                                                          │ /task_request
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  算法节点        │
                                                 │ (控制小车取药)   │
                                                 └─────────────────┘
```

| 角色 | 文件/组件 | 职责 |
|------|-----------|------|
| **前端** | index.html | 用户输入药品 ID 和数量，点击确认后发 POST 给后端 |
| **后端** | app.py | 校验药品、查坐标、写 order_log、发布 ROS2 任务 |
| **算法** | line_follower 或自研节点 | 订阅 /task_request，控制小车前往 (x,y) 取药 |

---

## 二、app.py 内部结构

### 1. 启动时（模块加载）

```
import Flask、sqlite3、json...
    │
    ├─▶ 启动 ROS2 后台线程 (init_ros2)
    │       └─▶ 创建节点 backend_task_publisher，发布者绑定 /task_request
    │
    ├─▶ 初始化 Flask，配置 CORS
    │
    └─▶ 准备数据库连接 (pharmacy.db)
```

### 2. 核心流程（用户点击「确认取药」后）

```
前端 POST /api/order  [{id:1, num:2}, {id:2, num:1}]
    │
    ├─▶ 1. 解析 JSON，校验每项都有 id、num
    │
    ├─▶ 2. 预校验：药品存在、未过期、库存充足
    │       └─▶ 任一项失败 → 返回 400 + error 给前端
    │
    ├─▶ 3. 全部通过 → 对每项：
    │       ├─ INSERT INTO order_log (status='pending', target_drug_id, quantity)
    │       └─ publish_task() 发布到 /task_request
    │
    └─▶ 4. 返回 {ok: true, task_ids: [1,2], message: "已下发 2 个取药任务"}
```

### 3. ROS2 发布内容格式

话题：`/task_request`  
类型：`std_msgs/String`  
内容（JSON 字符串）：
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

算法侧需解析 `msg.data` 的 JSON，根据 `x`、`y` 控制小车前往该坐标取药。

---

## 三、与前端的关系

| 前端动作 | 调用的 API | 后端行为 |
|----------|------------|----------|
| 页面加载时可选 | GET /api/drugs | 拉取药品列表（可扩展药品选择器） |
| 点击「确认取药」 | POST /api/order | 批量校验、入库、发 ROS2 任务 |

**前端请求示例**：
```javascript
fetch('http://localhost:5000/api/order', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify([{ id: 1, num: 2 }, { id: 2, num: 1 }])
});
```

**成功响应**：`{ ok: true, task_ids: [1, 2], message: "已下发 2 个取药任务" }`  
**失败响应**：`{ ok: false, error: "药品已过期: 维生素C" }` 等

---

## 四、与算法的关系

| 后端动作 | 算法侧需要做的 |
|----------|----------------|
| 发布到 /task_request | 订阅 /task_request |
| 消息格式：std_msgs/String，JSON | 解析 `msg.data`，提取 x、y、quantity |
| 每一条取药任务一条消息 | 按顺序或队列执行，控制小车前往 (x,y) |

**当前 line_follower**：只做巡线+红点停车，**未**订阅 /task_request。算法同学需要新增逻辑：订阅该话题，收到任务后规划路径并控制小车前往 (x, y)。

---

## 五、API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查，返回 `ros2` 是否已连接 |
| GET | /api/drugs | 列出所有药品 |
| GET | /api/orders | 查看取药记录（order_log） |
| POST | /api/order | 批量取药（前端用） |
| POST | /api/pickup | 单条取药（兼容） |

---

## 六、启动方式

```bash
# 1. 确保数据库已初始化
python3 init_db2.py

# 2. 启动 app.py
# 无 ROS2（仅入库，不发任务）：
python3 app.py

# 有 ROS2（入库 + 发布任务）：
source /opt/ros/jazzy/setup.bash
python3 app.py
```

---

## 七、数据流总结

```
用户在前端输入: 药品1 id=1 num=2, 药品2 id=2 num=1
        │
        ▼
    index.html 收集 → POST /api/order
        │
        ▼
    app.py: 校验 inventory 表 → 查 shelf_x, shelf_y
        │
        ├─▶ 写入 order_log (status=pending)
        │
        └─▶ 发布 /task_request (JSON)
                │
                ▼
            算法订阅 → 控制小车前往 (x,y) 取药
```

app.py 负责**业务逻辑**（校验、坐标、记录），算法负责**运动控制**（路径规划、执行取药）。
