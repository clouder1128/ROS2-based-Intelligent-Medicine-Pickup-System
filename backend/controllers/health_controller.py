"""
Health Controller
Provides health check endpoint for monitoring backend status
"""

from flask import Blueprint, jsonify
from utils.ros2_bridge import ros2_available

# Create blueprint for health routes
health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint

    Returns:
        JSON response with backend status and ROS2 availability
    """
    return jsonify({
        'success': True,
        'status': 'ok',
        'message': 'backend running',
        'ros2': ros2_available
    })