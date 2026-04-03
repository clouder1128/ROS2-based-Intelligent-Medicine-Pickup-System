# 后端 - 智能取药系统

接收前端请求 → 校验药品 → 写入取药记录 → **先扣减库存并提交事务** → 发布 ROS2 任务给算法节点控制小车；另有**按日历推进的过期清扫**线程，对仍有过期实物库存的药品发布清柜任务。

## 环境与依赖

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
# 1. 初始化数据库（会写入示例药品与过期清扫基准日 app_meta.expiry_sweep_date）
python3 init_db.py

# 2. 启动服务（若需 ROS2 下发任务，先 source 对应 ROS2 发行版的 setup.bash）
python3 app.py
```

服务监听 `http://0.0.0.0:5000`。

## 数据库说明

| 表 | 作用 |
|----|------|
| `inventory` | 药品：名称、可售 `quantity`、剩余天数 `expiry_date`（≤0 视为已超出保质期）、货架坐标等 |
| `order_log` | 取药任务记录（关联 `task_id`，状态含 `pending` 等） |
| `app_meta` | 键 `expiry_sweep_date`：由 **init_db 写入当天日期**，作为按日扣减 `expiry_date` 的日历锚点 |

每次执行 `init_db.py` 会重置示例数据并**刷新**清扫基准日为当日。旧库若无该键，后端首次清扫会仅补写当天、当日不扣减（兼容迁移）。

## 过期清扫（后台线程）

- 进程启动后由后台线程按间隔调用清扫逻辑；**默认每 3600 秒**检查一次，**同一自然日只会真正扣减一次**（按 `expiry_sweep_date` 与今天相差的天数一次性补扣，关机数日再开也不会丢天数）。
- 环境变量 **`EXPIRY_SWEEP_INTERVAL_SEC`** 可缩短间隔（例如本地测试设为 `60`）。
- 清扫步骤概览：对已过期的行将 `quantity` 置 0；**若某药品已过期且清仓前 `quantity > 0`**，在数据库提交后向 `/task_request` 发布 **`type: "expiry_removal"`**（见下文），通知算法将过期品取走。已为 0 的过期行不会重复发清柜消息。

## API 说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查（含 `ros2` 是否已连接） |
| GET | /api/drugs | 列出所有药品 |
| GET | /api/orders | 查看取药记录（最近 50 条） |
| POST | /api/order | 批量取药（前端常用） |
| POST | /api/pickup | 单条取药（兼容旧接口） |

### POST /api/order（批量）

**请求体**:

```json
[
  { "id": 1, "num": 2 },
  { "id": 2, "num": 1 }
]
```

**成功响应示例**:

```json
{
  "ok": true,
  "task_ids": [1, 2],
  "message": "已下发 2 个取药任务，库存已扣减"
}
```

下单成功时：**库存已在同一事务内扣减并提交**，再发布 ROS 任务；**当前未实现**算法节点回执后再扣减或失败回滚，仿真若常失败需前后端与算法再约定策略。

### ROS2 任务（话题 `/task_request`）

消息类型：`std_msgs/String`，负载为 **JSON 字符串**。算法需订阅该话题，并根据 **`type`** 分支处理。

**用户取药（`pickup`）** — 与 `order_log` 中 `task_id` 对应：

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

**过期清柜（`expiry_removal`）** — 由定期清扫触发，无订单 `task_id`：

```json
{
  "task_id": null,
  "type": "expiry_removal",
  "drug_id": 1,
  "name": "阿莫西林",
  "shelve_id": 1,
  "x": 1,
  "y": 1,
  "quantity": 10,
  "reason": "expired"
}
```

未安装 ROS2 或节点未连上时，后端仍写库；仅当 ROS2 发布器可用时才会向话题发布。

## 启动方式说明

- 推荐 **`python3 app.py`**：`debug=True` 且开启自动重载时，过期清扫线程仅在 **Werkzeug 子进程**（`WERKZEUG_RUN_MAIN=true`）中启动，避免父子进程各跑一套导致重复扣减。
- 若使用 **`flask run`**：建议开启 **debug（含重载）**，以便子进程带上 `WERKZEUG_RUN_MAIN` 并启动清扫线程；无重载的单进程场景需自行确认清扫线程是否符合预期。

## 前端对接

前端 `index.html` 可请求 `http://localhost:5000/api/order`。若前后端不同机，将前端中的 `API_BASE` 改为实际后端地址。
