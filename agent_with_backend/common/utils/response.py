"""
第一周：统一 API 响应格式工具

所有接口均返回以下结构：
成功：{"success": true, "data": {...}, "pagination": {...}, "error": null}
失败：{"success": false, "data": null, "pagination": null, "error": {"code": "...", "message": "..."}}

分页规范（与其他组件约定）：
  page     - 页码，从 1 开始（默认 1）
  limit    - 每页条数，最大 100（默认 20）
  total    - 总记录数
  pages    - 总页数
"""

import math
from typing import Any, Dict, List, Optional

from flask import jsonify


# ==================== 成功响应 ====================

def success_response(data: Any, message: str = None):
    """标准成功响应（无分页）"""
    body: Dict[str, Any] = {
        "success": True,
        "data": data,
        "pagination": None,
        "error": None,
    }
    if message:
        body["message"] = message
    return jsonify(body), 200


def paginated_response(data: List[Any], page: int, limit: int, total: int):
    """带分页的成功响应"""
    pages = math.ceil(total / limit) if limit > 0 else 0
    return jsonify({
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
        "error": None,
    }), 200


def created_response(data: Any, message: str = "创建成功"):
    """201 Created 响应"""
    return jsonify({
        "success": True,
        "data": data,
        "pagination": None,
        "error": None,
        "message": message,
    }), 201


# ==================== 错误响应 ====================

def error_response(code: str, message: str, status: int = 400):
    """标准错误响应"""
    return jsonify({
        "success": False,
        "data": None,
        "pagination": None,
        "error": {
            "code": code,
            "message": message,
        },
    }), status


def not_found_response(message: str = "资源不存在"):
    return error_response("NOT_FOUND", message, 404)


def bad_request_response(message: str = "请求参数错误"):
    return error_response("BAD_REQUEST", message, 400)


def internal_error_response(message: str = "服务器内部错误"):
    return error_response("INTERNAL_ERROR", message, 500)


def unauthorized_response(message: str = "未授权，请先登录"):
    return error_response("UNAUTHORIZED", message, 401)


def forbidden_response(message: str = "权限不足"):
    return error_response("FORBIDDEN", message, 403)


# ==================== 分页参数解析 ====================

def parse_pagination(args: Dict[str, str]) -> Dict[str, int]:
    """
    从请求参数中解析分页参数，返回 {"page": int, "limit": int, "offset": int}

    用法：
        params = parse_pagination(request.args)
        offset = params["offset"]
    """
    try:
        page = max(1, int(args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = min(100, max(1, int(args.get("limit", 20))))
    except (ValueError, TypeError):
        limit = 20

    return {
        "page": page,
        "limit": limit,
        "offset": (page - 1) * limit,
    }
