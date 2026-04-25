from typing import Any, Dict


def create_error_response(error_type: str, message: str) -> Dict[str, Any]:
    return {"success": False, "error_type": error_type, "message": message}


def create_success_response(data: Any) -> Dict[str, Any]:
    return {"success": True, "data": data}
