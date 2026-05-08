"""
组件1 第2周：数据验证规则

提供三类验证器：
  - validate_drug()       药品创建/更新（供组件2 POST/PUT /api/drugs 使用）
  - validate_category()   分类创建（供组件2 POST /api/categories 使用）
  - validate_inventory_transaction()  库存变更（供组件2 POST /api/drugs/<id>/adjust 使用）

统一返回格式：
  成功 → (True, {})
  失败 → (False, {"field": "错误说明", ...})
"""

import json
from typing import Any, Dict, List, Tuple

# ─────────────────────────────────────────
# 内部工具
# ─────────────────────────────────────────

def _require(errors: Dict, field: str, value: Any, message: str = None) -> bool:
    """字段不得为空（None / 空字符串）"""
    if value is None or (isinstance(value, str) and not value.strip()):
        errors[field] = message or f"{field} 不能为空"
        return False
    return True


def _max_len(errors: Dict, field: str, value: Any, max_length: int) -> bool:
    if isinstance(value, str) and len(value) > max_length:
        errors[field] = f"{field} 长度不能超过 {max_length} 个字符"
        return False
    return True


def _is_non_negative_int(errors: Dict, field: str, value: Any) -> bool:
    try:
        v = int(value)
        if v < 0:
            errors[field] = f"{field} 不能为负数"
            return False
    except (TypeError, ValueError):
        errors[field] = f"{field} 必须为整数"
        return False
    return True


def _in_choices(errors: Dict, field: str, value: Any, choices: List) -> bool:
    if value not in choices:
        errors[field] = f"{field} 必须是以下值之一: {choices}"
        return False
    return True


# ─────────────────────────────────────────
# 药品验证
# ─────────────────────────────────────────

# 允许的剂型值
DOSAGE_FORM_CHOICES = [
    "片剂", "胶囊", "口服液", "注射液", "颗粒剂",
    "软膏", "乳膏", "贴片", "滴眼液", "滴鼻液",
    "栓剂", "糖浆", "丸剂", "散剂", "喷雾剂", "其他",
]

# 允许的孕期分级
PREGNANCY_CATEGORY_CHOICES = ["A", "B", "C", "D", "X", ""]

# 允许的单位
UNIT_CHOICES = ["盒", "瓶", "支", "片", "粒", "袋", "管", "贴", "个", "克", "毫升"]

# 与 api/drug_controller 写入前截断规则一致
# （《五人团队分工方案（修订版）》组件1：完整数据验证 + POST/PUT 共用）
DRUG_NAME_MAX_LEN = 500
DRUG_CATEGORY_MAX_LEN = 200
DRUG_OPTIONAL_STR_MAX_LEN = 2000
DRUG_STRENGTH_MAX_LEN = 100
DRUG_JSON_TEXT_MAX_LEN = 65535
INDICATION_ITEM_MAX_LEN = 500


def _is_any_int(errors: Dict, field: str, value: Any) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        errors[field] = f"{field} 必须为整数"
        return False


def _is_non_negative_float(errors: Dict, field: str, value: Any) -> bool:
    try:
        v = float(value)
        if v < 0:
            errors[field] = f"{field} 不能为负数"
            return False
    except (TypeError, ValueError):
        errors[field] = f"{field} 必须为有效数字"
        return False
    return True


def _validate_indications(errors: Dict, data: Dict[str, Any]) -> None:
    if "indications" not in data:
        return
    inds = data["indications"]
    if inds is None:
        return
    if not isinstance(inds, list):
        errors["indications"] = "indications 必须为列表"
        return
    for i, item in enumerate(inds):
        if not isinstance(item, str):
            errors["indications"] = f"indications[{i}] 必须为字符串"
            return
        if len(item.strip()) > INDICATION_ITEM_MAX_LEN:
            errors["indications"] = (
                f"indications[{i}] 长度不能超过 {INDICATION_ITEM_MAX_LEN}"
            )
            return


def _validate_jsonish_column(errors: Dict, field: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        _max_len(errors, field, value, DRUG_JSON_TEXT_MAX_LEN)
        return
    if isinstance(value, (list, dict)):
        try:
            s = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            errors[field] = f"{field} 无法序列化为 JSON"
            return
        if len(s) > DRUG_JSON_TEXT_MAX_LEN:
            errors[field] = (
                f"{field} 序列化后长度不能超过 {DRUG_JSON_TEXT_MAX_LEN}"
            )
        return
    errors[field] = f"{field} 须为字符串、数组或对象"


def validate_drug(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Dict[str, str]]:
    """
    验证药品创建（is_update=False）或更新（is_update=True）的请求体。

    规则与 `api/drug_controller` 中 POST /api/drugs、PUT /api/drugs/<id> 对齐；
    创建时必填：name, quantity, expiry_date, shelf_x, shelf_y, shelve_id。

    Returns:
        (True, {})                  — 验证通过
        (False, {"field": "msg"})   — 验证失败，含所有错误
    """
    errors: Dict[str, str] = {}

    _validate_indications(errors, data)

    if not is_update:
        for field in (
            "name",
            "quantity",
            "expiry_date",
            "shelf_x",
            "shelf_y",
            "shelve_id",
        ):
            if field not in data:
                errors[field] = f"{field} 为必填项"

    if "name" in data:
        n = data["name"]
        if not isinstance(n, str) or not n.strip():
            errors["name"] = "name 必须为非空字符串"
        else:
            _max_len(errors, "name", n, DRUG_NAME_MAX_LEN)

    for field in ("quantity", "stock"):
        if field in data:
            _is_non_negative_int(errors, field, data[field])

    for field in ("expiry_date", "shelf_x", "shelf_y", "shelve_id"):
        if field in data:
            _is_any_int(errors, field, data[field])

    if "category" in data and data["category"] is not None:
        _max_len(
            errors,
            "category",
            str(data["category"]).strip(),
            DRUG_CATEGORY_MAX_LEN,
        )

    optional_str_fields_2000 = (
        "generic_name",
        "description",
        "manufacturer",
        "specification",
        "dosage_form",
        "unit",
        "pack_size",
        "approval_number",
        "barcode",
        "storage_condition",
        "usage_dosage",
        "contraindications",
        "side_effects",
        "interaction_warning",
        "pregnancy_category",
        "pediatric_caution",
        "supplier",
        "country_of_origin",
        "image_url",
    )
    for field in optional_str_fields_2000:
        if field in data and data[field] is not None:
            if not isinstance(data[field], str):
                errors[field] = f"{field} 必须为字符串"
            else:
                _max_len(errors, field, data[field], DRUG_OPTIONAL_STR_MAX_LEN)

    if "strength" in data and data["strength"] is not None:
        raw = data["strength"]
        s = raw.strip() if isinstance(raw, str) else str(raw).strip()
        _max_len(errors, "strength", s, DRUG_STRENGTH_MAX_LEN)

    for field in ("min_stock_level", "max_stock_level", "min_stock_alert"):
        if field in data:
            _is_non_negative_int(errors, field, data[field])

    min_v = data.get("min_stock_level")
    max_v = data.get("max_stock_level")
    if min_v is not None and max_v is not None and "min_stock_level" not in errors \
            and "max_stock_level" not in errors:
        try:
            if int(min_v) > int(max_v):
                errors["min_stock_level"] = "min_stock_level 不能大于 max_stock_level"
        except (TypeError, ValueError):
            pass

    for field in ("retail_price", "cost_price", "purchase_price"):
        if field in data:
            _is_non_negative_float(errors, field, data[field])

    if "dosage_form" in data and data["dosage_form"]:
        if isinstance(data["dosage_form"], str):
            _in_choices(
                errors, "dosage_form", data["dosage_form"], DOSAGE_FORM_CHOICES
            )

    if "pregnancy_category" in data and data["pregnancy_category"] is not None:
        pc = data["pregnancy_category"]
        if isinstance(pc, str):
            _in_choices(
                errors,
                "pregnancy_category",
                pc,
                PREGNANCY_CATEGORY_CHOICES,
            )
        else:
            errors["pregnancy_category"] = "pregnancy_category 必须为字符串"

    if "unit" in data and data["unit"]:
        if isinstance(data["unit"], str):
            _in_choices(errors, "unit", data["unit"], UNIT_CHOICES)

    if "is_prescription" in data:
        iv = data["is_prescription"]
        _ok = iv in (0, 1, True, False, "0", "1")
        if not _ok and isinstance(iv, str) and iv.lower() in ("true", "false"):
            _ok = True
        if not _ok:
            errors["is_prescription"] = "is_prescription 必须为 0、1 或 true/false"

    for col in ("drug_interactions", "age_restrictions"):
        if col in data:
            _validate_jsonish_column(errors, col, data[col])

    return (len(errors) == 0), errors


# ─────────────────────────────────────────
# 分类验证
# ─────────────────────────────────────────

def validate_category(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Dict[str, str]]:
    """
    验证分类创建（POST /api/categories）或更新请求体。

    Returns:
        (True, {})  or  (False, {"field": "msg"})
    """
    errors: Dict[str, str] = {}

    if not is_update:
        _require(errors, "name", data.get("name"))

    if "name" in data:
        _require(errors, "name", data["name"])
        _max_len(errors, "name", data["name"], 50)

    if "description" in data and data["description"] is not None:
        _max_len(errors, "description", data["description"], 500)

    if "sort_order" in data and data["sort_order"] is not None:
        _is_non_negative_int(errors, "sort_order", data["sort_order"])

    if "parent_id" in data and data["parent_id"] is not None:
        try:
            pid = int(data["parent_id"])
            if pid <= 0:
                errors["parent_id"] = "parent_id 必须为正整数"
        except (TypeError, ValueError):
            errors["parent_id"] = "parent_id 必须为整数"

    return (len(errors) == 0), errors


# ─────────────────────────────────────────
# 库存变更验证
# ─────────────────────────────────────────

TRANSACTION_TYPE_CHOICES = ["in", "out", "adjust", "expire"]


def validate_inventory_transaction(data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """
    验证库存变更请求体（POST /api/drugs/<id>/adjust）。

    必填: quantity_change, transaction_type
    可选: reason, operator

    字段名与接口清单及 inventory_transactions 表保持一致：
      quantity_change  — 变化量（非零整数）
      transaction_type — 'in' / 'out' / 'adjust' / 'expire'

    Returns:
        (True, {})  or  (False, {"field": "msg"})
    """
    errors: Dict[str, str] = {}

    # quantity_change 必填，且为非零整数
    if not _require(errors, "quantity_change", data.get("quantity_change")):
        pass
    elif "quantity_change" in data:
        try:
            v = int(data["quantity_change"])
            if v == 0:
                errors["quantity_change"] = "quantity_change 不能为 0"
        except (TypeError, ValueError):
            errors["quantity_change"] = "quantity_change 必须为整数"

    # transaction_type 必填
    if _require(errors, "transaction_type", data.get("transaction_type")):
        _in_choices(errors, "transaction_type", data["transaction_type"], TRANSACTION_TYPE_CHOICES)

    # reason 可选，但有长度限制
    if "reason" in data:
        _max_len(errors, "reason", data["reason"], 500)

    # operator 可选，长度限制
    if "operator" in data:
        _max_len(errors, "operator", data["operator"], 100)

    return (len(errors) == 0), errors


# ─────────────────────────────────────────
# 分页参数验证（通用）
# ─────────────────────────────────────────

def validate_pagination_params(args: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """
    验证 page / limit 查询参数是否合法。

    与 response.parse_pagination 配合使用：先验证，再解析。
    """
    errors: Dict[str, str] = {}

    if "page" in args:
        try:
            if int(args["page"]) < 1:
                errors["page"] = "page 必须为正整数"
        except (TypeError, ValueError):
            errors["page"] = "page 必须为整数"

    if "limit" in args:
        try:
            v = int(args["limit"])
            if v < 1 or v > 100:
                errors["limit"] = "limit 必须在 1~100 之间"
        except (TypeError, ValueError):
            errors["limit"] = "limit 必须为整数"

    return (len(errors) == 0), errors
