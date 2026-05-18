"""审计日志写入。"""

from __future__ import annotations

import json
from typing import Any, Optional

from auth.db import get_db_connection


def write_audit(
    *,
    user_id: Optional[int],
    username: Optional[str],
    action: str,
    resource: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    details_s = json.dumps(details, ensure_ascii=False) if details else None
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO auth_audit_logs (user_id, username, action, resource, details, ip)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, action, resource, details_s, ip),
        )
        conn.commit()
    finally:
        conn.close()
