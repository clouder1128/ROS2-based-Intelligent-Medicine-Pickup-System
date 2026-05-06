"""RBAC：角色与权限码（与架构接口清单及药品 API 权限矩阵一致）。"""

from __future__ import annotations

# 角色 code（存储于 auth_roles.code）
ROLE_ADMIN = "admin"
ROLE_PHARMACIST = "pharmacist"
ROLE_DOCTOR = "doctor"
ROLE_PATIENT = "patient"

# 权限 code（与接口清单细粒度一致）
PERM_READ_DRUG = "read:drug"
PERM_CREATE_DRUG = "create:drug"
PERM_UPDATE_DRUG = "update:drug"
PERM_DELETE_DRUG = "delete:drug"
PERM_READ_INVENTORY = "read:inventory"
PERM_UPDATE_INVENTORY = "update:inventory"
PERM_READ_USERS = "read:users"
PERM_WRITE_USERS = "write:users"
PERM_READ_AUDIT = "read:audit"

ALL_PERMISSION_CODES: tuple[str, ...] = (
    PERM_READ_DRUG,
    PERM_CREATE_DRUG,
    PERM_UPDATE_DRUG,
    PERM_DELETE_DRUG,
    PERM_READ_INVENTORY,
    PERM_UPDATE_INVENTORY,
    PERM_READ_USERS,
    PERM_WRITE_USERS,
    PERM_READ_AUDIT,
)

ROLE_PERMISSION_MAP: dict[str, frozenset[str]] = {
    ROLE_ADMIN: frozenset(ALL_PERMISSION_CODES),
    ROLE_PHARMACIST: frozenset(
        {
            PERM_READ_DRUG,
            PERM_CREATE_DRUG,
            PERM_UPDATE_DRUG,
            PERM_READ_INVENTORY,
            PERM_UPDATE_INVENTORY,
        }
    ),
    ROLE_DOCTOR: frozenset({PERM_READ_DRUG}),
    ROLE_PATIENT: frozenset({PERM_READ_DRUG}),
}
