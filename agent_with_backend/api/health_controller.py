"""
Health Controller
Provides health check endpoint for monitoring backend status
"""

from flask import Blueprint, jsonify
from ros_integration.bridge import check_ros2_status

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    ros2_status = check_ros2_status()

    return jsonify(
        {
            "success": True,
            "status": "ok",
            "message": "backend running",
            "ros2": ros2_status.get("available", False),
            "details": {
                "ros2_integration": ros2_status
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
