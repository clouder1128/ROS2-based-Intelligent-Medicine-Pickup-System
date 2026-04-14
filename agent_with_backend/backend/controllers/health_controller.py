"""
Health Controller
Provides health check endpoint for monitoring backend status
"""

from flask import Blueprint, jsonify
from utils.ros2_bridge import check_ros2_status

# Create blueprint for health routes
health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint

    Returns:
        JSON response with backend status and ROS2 availability
    """
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
    """ROS2-specific health check endpoint

    Returns:
        Detailed ROS2 integration status
    """
    ros2_status = check_ros2_status()

    return jsonify(
        {
            "success": True,
            "ros2": ros2_status,
            "integration_mode": ros2_status.get("integration", "unknown")
        }
    )
