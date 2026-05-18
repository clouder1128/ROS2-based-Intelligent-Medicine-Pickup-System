"""
ROS2 状态 API 控制器
提供 Unity 仿真实时状态的 HTTP 查询端点。
"""

from flask import Blueprint, jsonify

from ros_integration.state_store import RosStateStore

ros_state_bp = Blueprint("ros_state", __name__, url_prefix="/api")

_store = RosStateStore()


@ros_state_bp.route("/ros/car-states", methods=["GET"])
def get_car_states():
    """获取所有 AGV 小车最新状态"""
    return jsonify({"success": True, "data": _store.get_all_cars()})


@ros_state_bp.route("/ros/task-states", methods=["GET"])
def get_task_states():
    """获取所有任务最新状态"""
    return jsonify({"success": True, "data": _store.get_all_tasks()})


@ros_state_bp.route("/ros/task-states/<task_id>", methods=["GET"])
def get_task_state(task_id: str):
    """获取指定任务状态"""
    state = _store.get_task(task_id)
    if state is None:
        return jsonify({"success": False, "error": "task not found", "code": "NOT_FOUND"}), 404
    return jsonify({"success": True, "data": state})


@ros_state_bp.route("/ros/cabinet-states", methods=["GET"])
def get_cabinet_states():
    """获取所有药柜库存状态"""
    return jsonify({"success": True, "data": _store.get_all_cabinets()})


@ros_state_bp.route("/ros/return-to-queue", methods=["POST"])
def return_to_queue():
    """通知 ROS2 小车返回初始队列"""
    try:
        from ros_integration.bridge import publish_return_to_queue
        publish_return_to_queue()
        return jsonify({"success": True, "message": "Return-to-queue command published"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "code": "ROS_ERROR"}), 500


@ros_state_bp.route("/ros/status", methods=["GET"])
def get_ros_status():
    """获取 ROS2 连接概览状态"""
    connected = _store.is_connected()
    cars = _store.get_all_cars()
    tasks = _store.get_all_tasks()
    return jsonify({
        "success": True,
        "data": {
            "connected": connected,
            "car_count": len(cars),
            "active_tasks": sum(1 for t in tasks if t.get("task_state", 0) == 1),
            "cars": cars,
            "tasks": tasks,
        },
    })
