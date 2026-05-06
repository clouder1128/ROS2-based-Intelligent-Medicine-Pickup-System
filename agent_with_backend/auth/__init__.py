"""权限认证系统（组件4）：JWT、RBAC、审计日志、接口清单实现。"""

from auth.blueprint import auth_bp
from auth.constants import (
    PERM_CREATE_DRUG,
    PERM_DELETE_DRUG,
    PERM_READ_AUDIT,
    PERM_READ_DRUG,
    PERM_READ_INVENTORY,
    PERM_READ_USERS,
    PERM_UPDATE_DRUG,
    PERM_UPDATE_INVENTORY,
    PERM_WRITE_USERS,
)
from auth.middleware import require_auth, require_permissions

__all__ = [
    "auth_bp",
    "require_auth",
    "require_permissions",
    "PERM_READ_DRUG",
    "PERM_CREATE_DRUG",
    "PERM_UPDATE_DRUG",
    "PERM_DELETE_DRUG",
    "PERM_READ_INVENTORY",
    "PERM_UPDATE_INVENTORY",
    "PERM_READ_USERS",
    "PERM_WRITE_USERS",
    "PERM_READ_AUDIT",
]
