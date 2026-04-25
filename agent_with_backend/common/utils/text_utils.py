import time
import logging
import hashlib
import re
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager
from datetime import datetime


def truncate_text(text: str, max_len: int = 500) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def estimate_tokens(text: str) -> int:
    return len(text) // 4


@contextmanager
def log_duration(logger_obj: logging.Logger, operation: str):
    start = time.time()
    yield
    elapsed = time.time() - start
    logger_obj.info(f"{operation} took {elapsed:.2f}s")


def generate_id(prefix: str) -> str:
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    return f"{prefix}-{date_part}-{time_part}"


def hash_string(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()[:8]


def now_iso() -> str:
    return datetime.now().isoformat()


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def merge_dicts(base: Dict, updates: Dict) -> Dict:
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def validate_patient_input(text: str) -> Dict[str, Any]:
    if not text or not isinstance(text, str):
        return {"valid": False, "error": "Input cannot be empty"}
    cleaned = text.strip()
    if len(cleaned) < 2:
        return {"valid": False, "error": "Input too short"}
    sensitive_words = ["suicide", "drugs"]
    for word in sensitive_words:
        if word in cleaned:
            return {"valid": False, "error": f"Input contains sensitive word: {word}"}
    return {"valid": True, "cleaned": cleaned}


def extract_mentions_of_allergy(text: str) -> List[str]:
    allergy_keywords = ["penicillin", "cephalosporin", "sulfa", "aspirin"]
    found = []
    for kw in allergy_keywords:
        if kw in text:
            found.append(kw)
    return found


def summarize_conversation(messages: List[Dict], max_summary_tokens: int = 200) -> str:
    user_messages = [m.get("content", "") for m in messages if m.get("role") == "user"]
    if not user_messages:
        return "No conversation records"
    summary = "Patient requests: " + "; ".join(
        [truncate_text(um, 50) for um in user_messages[-3:]]
    )
    return truncate_text(summary, max_summary_tokens)


def estimate_cost(tokens: int, model: str = "claude-3-sonnet") -> float:
    pricing = {
        "claude-3-sonnet": 0.003,
        "claude-3-opus": 0.015,
        "gpt-4": 0.03,
        "gpt-3.5-turbo": 0.001,
    }
    price_per_1k = pricing.get(model, 0.003)
    return (tokens / 1000) * price_per_1k
