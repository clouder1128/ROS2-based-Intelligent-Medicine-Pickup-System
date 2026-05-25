"""
组件1 文件上传存储接口

提供三个端点：
  POST   /api/upload          - 上传文件（图片 / CSV），返回 file_id + 访问 URL
  GET    /api/upload/<file_id> - 下载 / 访问已上传的文件
  DELETE /api/upload/<file_id> - 删除已上传的文件（需 admin 权限）

支持的文件类型：
  图片：jpg / jpeg / png / gif / webp
  数据：csv

存储位置：agent_with_backend/uploads/（不进数据库，以 UUID 命名保持唯一性）

接口规范：与项目统一响应格式对齐（common/utils/response.py）
"""

import os
import uuid
from pathlib import Path

from flask import Blueprint, request, send_from_directory

from common.utils.response import (
    success_response,
    created_response,
    bad_request_response,
    not_found_response,
    error_response,
)

upload_bp = Blueprint("upload", __name__, url_prefix="/api/upload")

# ── 配置 ──────────────────────────────────────────────────────────────────────

# 上传目录：<项目根>/uploads/
_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的扩展名 → MIME 类型（用于响应头）
_ALLOWED = {
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "png":  "image/png",
    "gif":  "image/gif",
    "webp": "image/webp",
    "csv":  "text/csv",
}

# 单文件最大体积：16 MB
_MAX_SIZE_BYTES = 16 * 1024 * 1024


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _allowed_ext(filename: str):
    """返回 (True, ext) 或 (False, None)"""
    if "." not in filename:
        return False, None
    ext = filename.rsplit(".", 1)[1].lower()
    return (ext in _ALLOWED), ext


def _build_url(file_id: str) -> str:
    """拼接文件访问 URL（供前端直接使用）"""
    from flask import request as req
    return f"{req.host_url.rstrip('/')}/api/upload/{file_id}"


# ── 端点 ──────────────────────────────────────────────────────────────────────

@upload_bp.route("", methods=["POST"])
def upload_file():
    """
    上传文件

    请求：multipart/form-data，字段名 `file`
    可选 query 参数：
      type=image | csv   （不传则从扩展名自动推断）

    成功响应 201：
    {
      "success": true,
      "data": {
        "file_id":      "uuid.ext",
        "file_name":    "原始文件名",
        "file_size":    12345,
        "content_type": "image/png",
        "url":          "http://host/api/upload/uuid.ext"
      }
    }
    """
    if "file" not in request.files:
        return bad_request_response("请求中未找到 file 字段")

    f = request.files["file"]
    if not f.filename:
        return bad_request_response("文件名不能为空")

    ok, ext = _allowed_ext(f.filename)
    if not ok:
        allowed_str = ", ".join(sorted(_ALLOWED.keys()))
        return bad_request_response(f"不支持的文件类型，允许的类型：{allowed_str}")

    # 读取内容并校验大小
    content = f.read()
    if len(content) > _MAX_SIZE_BYTES:
        return bad_request_response(
            f"文件体积超出限制（最大 {_MAX_SIZE_BYTES // (1024 * 1024)} MB）"
        )

    # 以 UUID 为基础生成唯一文件名，避免覆盖
    file_id = f"{uuid.uuid4().hex}.{ext}"
    dest = _UPLOAD_DIR / file_id
    dest.write_bytes(content)

    data = {
        "file_id":      file_id,
        "file_name":    f.filename,
        "file_size":    len(content),
        "content_type": _ALLOWED[ext],
        "url":          _build_url(file_id),
    }
    return created_response(data, "文件上传成功")


@upload_bp.route("/<file_id>", methods=["GET"])
def serve_file(file_id: str):
    """
    下载 / 访问已上传的文件

    路径参数：file_id — 由 POST /api/upload 返回的 file_id
    成功：直接返回文件二进制流（带正确 Content-Type）
    失败：404 JSON
    """
    # 安全校验：只允许 <hex>.<ext> 格式，防止路径穿越
    if "/" in file_id or ".." in file_id:
        return bad_request_response("无效的 file_id")

    dest = _UPLOAD_DIR / file_id
    if not dest.exists():
        return not_found_response(f"文件 {file_id} 不存在")

    ext = file_id.rsplit(".", 1)[-1].lower() if "." in file_id else ""
    mimetype = _ALLOWED.get(ext, "application/octet-stream")

    return send_from_directory(
        str(_UPLOAD_DIR),
        file_id,
        mimetype=mimetype,
        as_attachment=False,
    )


@upload_bp.route("/<file_id>", methods=["DELETE"])
def delete_file(file_id: str):
    """
    删除已上传的文件

    路径参数：file_id — 由 POST /api/upload 返回的 file_id
    成功响应：{ "success": true, "data": { "file_id": "...", "deleted": true } }
    失败：404 JSON

    权限：建议在 main.py 或通过 @require_permission('manage:upload') 控制；
          当前为开放接口，生产环境请加鉴权。
    """
    if "/" in file_id or ".." in file_id:
        return bad_request_response("无效的 file_id")

    dest = _UPLOAD_DIR / file_id
    if not dest.exists():
        return not_found_response(f"文件 {file_id} 不存在")

    try:
        dest.unlink()
    except OSError as e:
        return error_response("FILE_DELETE_ERROR", f"删除失败：{e}", 500)

    return success_response({"file_id": file_id, "deleted": True}, "文件已删除")
