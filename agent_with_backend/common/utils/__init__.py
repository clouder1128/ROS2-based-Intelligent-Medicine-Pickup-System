# 第一周：暴露统一响应格式工具，方便其他组件直接 from common.utils import ...
from .response import (
    success_response,
    paginated_response,
    created_response,
    error_response,
    not_found_response,
    bad_request_response,
    internal_error_response,
    unauthorized_response,
    forbidden_response,
    parse_pagination,
)

# 第二周：暴露数据验证工具（与 api/drug_controller POST/PUT /api/drugs 共用同一套规则）
from .validation import (
    validate_drug,
    validate_category,
    validate_inventory_transaction,
    validate_pagination_params,
    DRUG_NAME_MAX_LEN,
    DRUG_CATEGORY_MAX_LEN,
    DRUG_OPTIONAL_STR_MAX_LEN,
    DRUG_STRENGTH_MAX_LEN,
    DRUG_JSON_TEXT_MAX_LEN,
    INDICATION_ITEM_MAX_LEN,
)

__all__ = [
    # response
    "success_response",
    "paginated_response",
    "created_response",
    "error_response",
    "not_found_response",
    "bad_request_response",
    "internal_error_response",
    "unauthorized_response",
    "forbidden_response",
    "parse_pagination",
    # validation
    "validate_drug",
    "validate_category",
    "validate_inventory_transaction",
    "validate_pagination_params",
    "DRUG_NAME_MAX_LEN",
    "DRUG_CATEGORY_MAX_LEN",
    "DRUG_OPTIONAL_STR_MAX_LEN",
    "DRUG_STRENGTH_MAX_LEN",
    "DRUG_JSON_TEXT_MAX_LEN",
    "INDICATION_ITEM_MAX_LEN",
]
