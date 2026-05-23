"""
Health Controller
Provides health check endpoint for monitoring backend status
"""

from flask import Blueprint, jsonify
from ros_integration.bridge import check_ros2_status
from common.utils.cache import get_drug_cache

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    ros2_status = check_ros2_status()
    cache_info = get_drug_cache().info()

    return jsonify(
        {
            "success": True,
            "status": "ok",
            "message": "backend running",
            "ros2": ros2_status.get("available", False),
            "details": {
                "ros2_integration": ros2_status,
                "cache": cache_info,   # 组件1第3周：缓存运行状态（active_keys / expired_keys / TTL 配置）
            }
        }
    )


@health_bp.route("/health/ros2", methods=["GET"])
def health_ros2():
    ros2_status = check_ros2_status()

    return jsonify(
        {
            "success": True,
            "ros2": ros2_status,
            "integration_mode": ros2_status.get("integration", "unknown")
        }
    )
