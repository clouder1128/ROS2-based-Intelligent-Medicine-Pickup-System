"""
审批单管理：SQLite 表 approvals，供 AI 开药助手等场景使用（与 Flask 取药后端可共用同一 pharmacy.db）。

典型流程：create → pending → approve / reject → 业务侧再调药房配药。

环境变量:
    APPROVAL_DB_PATH  数据库路径；默认与本文件同目录下的 pharmacy.db。
"""

from __future__ import annotations

import logging
import os
import secrets
import sqlite3
import threading
from datetime import date, datetime, timezone
from typing import Any

_logger = logging.getLogger(__name__)

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "pharmacy.db")
_lock = threading.Lock()


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_approval_id() -> str:
    d = date.today().isoformat().replace("-", "")
    return f"AP-{d}-{secrets.token_hex(4).upper()}"


class ApprovalManager:
    """审批单 CRUD；表不存在时自动创建。"""

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.environ.get("APPROVAL_DB_PATH", _DEFAULT_DB)
        self._table_ready = False

    def ensure_table(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                patient_name TEXT NOT NULL,
                patient_age INTEGER,
                patient_weight REAL,
                symptoms TEXT,
                advice TEXT NOT NULL,
                drug_name TEXT,
                drug_type TEXT,
                quantity INTEGER DEFAULT 1,
                status TEXT NOT NULL,
                doctor_id TEXT,
                reject_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                approved_at DATETIME
            )
        """)
        try:
            conn.execute("ALTER TABLE approvals ADD COLUMN quantity INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_approvals_created ON approvals(created_at DESC)"
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if not self._table_ready:
            self.ensure_table(conn)
            conn.commit()
            self._table_ready = True
        return conn

    def create(
        self,
        patient_name: str,
        advice: str,
        *,
        patient_age: int | None = None,
        patient_weight: float | None = None,
        symptoms: str | None = None,
        drug_name: str | None = None,
        drug_type: str | None = None,
        quantity: int = 1,
    ) -> str:
        aid = _new_approval_id()
        with _lock:
            conn = self._connect()
            try:
                conn.execute(
                    """INSERT INTO approvals (
                        id, patient_name, patient_age, patient_weight, symptoms,
                        advice, drug_name, drug_type, quantity, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        aid,
                        patient_name,
                        patient_age,
                        patient_weight,
                        symptoms,
                        advice,
                        drug_name,
                        drug_type,
                        quantity,
                        self.STATUS_PENDING,
                    ),
                )
                conn.commit()
                return aid
            finally:
                conn.close()

    def get(self, approval_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            cur = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_pending(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        conn = self._connect()
        try:
            cur = conn.execute(
                """SELECT * FROM approvals WHERE status = ?
                   ORDER BY created_at ASC LIMIT ?""",
                (self.STATUS_PENDING, limit),
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def approve(self, approval_id: str, doctor_id: str, notes: str = None) -> bool:
        with _lock:
            conn = self._connect()
            try:
                if notes:
                    cur = conn.execute(
                        "SELECT advice FROM approvals WHERE id = ?", (approval_id,)
                    )
                    row = cur.fetchone()
                    if row:
                        new_advice = row["advice"] + "\n[doctor] " + notes
                        cur = conn.execute(
                            """UPDATE approvals SET status = ?, doctor_id = ?, approved_at = ?, advice = ?
                               WHERE id = ? AND status = ?""",
                            (
                                self.STATUS_APPROVED,
                                doctor_id,
                                _utc_iso(),
                                new_advice,
                                approval_id,
                                self.STATUS_PENDING,
                            ),
                        )
                    else:
                        return False
                else:
                    cur = conn.execute(
                        """UPDATE approvals SET status = ?, doctor_id = ?, approved_at = ?
                           WHERE id = ? AND status = ?""",
                        (
                            self.STATUS_APPROVED,
                            doctor_id,
                            _utc_iso(),
                            approval_id,
                            self.STATUS_PENDING,
                        ),
                    )
                conn.commit()
                return cur.rowcount == 1
            finally:
                conn.close()

    def reject(self, approval_id: str, doctor_id: str, reason: str) -> bool:
        with _lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    """UPDATE approvals SET status = ?, doctor_id = ?, reject_reason = ?, approved_at = ?
                       WHERE id = ? AND status = ?""",
                    (
                        self.STATUS_REJECTED,
                        doctor_id,
                        reason,
                        _utc_iso(),
                        approval_id,
                        self.STATUS_PENDING,
                    ),
                )
                conn.commit()
                return cur.rowcount == 1
            finally:
                conn.close()


_singleton: ApprovalManager | None = None


def get_approval_manager(db_path: str | None = None) -> ApprovalManager:
    global _singleton
    if _singleton is None:
        _singleton = ApprovalManager(db_path)
    return _singleton
