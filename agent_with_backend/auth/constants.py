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
PERM_BATCH_DRUG = "batch:drug"
PERM_READ_APPROVAL = "read:approval"
PERM_APPROVE_APPROVAL = "approve:approval"
PERM_REJECT_APPROVAL = "reject:approval"
PERM_READ_ORDER = "read:order"

ALL_PERMISSION_CODES: tuple[str, ...] = (
    PERM_READ_DRUG,
    PERM_CREATE_DRUG,
    PERM_UPDATE_DRUG,
    PERM_DELETE_DRUG,
    PERM_READ_INVENTORY,
    PERM_UPDATE_INVENTORY,
    PERM_BATCH_DRUG,
    PERM_READ_APPROVAL,
    PERM_APPROVE_APPROVAL,
    PERM_REJECT_APPROVAL,
    PERM_READ_ORDER,
    PERM_READ_USERS,
    PERM_WRITE_USERS,
    PERM_READ_AUDIT,
)

# 与分工文档权限矩阵一致（auth_permissions.description）
PERMISSION_DESCRIPTIONS: dict[str, str] = {
    PERM_READ_DRUG: "读取药品",
    PERM_CREATE_DRUG: "创建药品",
    PERM_UPDATE_DRUG: "更新药品",
    PERM_DELETE_DRUG: "删除药品",
    PERM_READ_INVENTORY: "读取库存",
    PERM_UPDATE_INVENTORY: "调整库存",
    PERM_BATCH_DRUG: "批量导入药品",
    PERM_READ_APPROVAL: "读取审批",
    PERM_APPROVE_APPROVAL: "通过审批",
    PERM_REJECT_APPROVAL: "驳回审批",
    PERM_READ_ORDER: "读取订单",
    PERM_READ_USERS: "查询用户",
    PERM_WRITE_USERS: "维护用户",
    PERM_READ_AUDIT: "审计日志",
}

ROLE_PERMISSION_MAP: dict[str, frozenset[str]] = {
    ROLE_ADMIN: frozenset(ALL_PERMISSION_CODES),
    ROLE_PHARMACIST: frozenset(
        {
            PERM_READ_DRUG,
            PERM_CREATE_DRUG,
            PERM_UPDATE_DRUG,
            PERM_READ_INVENTORY,
            PERM_UPDATE_INVENTORY,
            PERM_READ_ORDER,
        }
    ),
    ROLE_DOCTOR: frozenset(
        {
            PERM_READ_DRUG,
            PERM_READ_INVENTORY,
            PERM_READ_APPROVAL,
            PERM_APPROVE_APPROVAL,
            PERM_REJECT_APPROVAL,
            PERM_READ_ORDER,
        }
    ),
    ROLE_PATIENT: frozenset({PERM_READ_DRUG}),
}
