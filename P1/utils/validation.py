# validation.py
"""验证和响应格式工具函数"""

from typing import Any, Dict


def create_error_response(error_type: str, message: str) -> Dict[str, Any]:
    """生成统一的错误响应格式"""
    return {
        "success": False,
        "error_type": error_type,
        "message": message
    }


def create_success_response(data: Any) -> Dict[str, Any]:
    """生成统一的成功响应格式"""
    return {
        "success": True,
        "data": data
    }


__all__ = ['create_error_response', 'create_success_response']