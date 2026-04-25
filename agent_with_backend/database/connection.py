import sqlite3
import json
import os
from datetime import date, datetime
from typing import Any, Dict, Optional, Union

from common.config import Config


def get_db_connection() -> sqlite3.Connection:
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            stock INTEGER DEFAULT 0,
            shelf_location TEXT,
            expiry_date DATE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            drug_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (drug_id) REFERENCES inventory (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            drug_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            duration TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            doctor_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        sample_drugs = [
            ("Aspirin", "Pain reliever", 100, "A1", "2026-12-31"),
            ("Ibuprofen", "Anti-inflammatory", 50, "B2", "2026-10-15"),
            ("Amoxicillin", "Antibiotic", 30, "C3", "2026-08-20"),
            ("Paracetamol", "Fever reducer", 80, "A2", "2026-11-30"),
        ]
        cursor.executemany(
            """
            INSERT INTO inventory (name, description, stock, shelf_location, expiry_date)
            VALUES (?, ?, ?, ?, ?)
        """,
            sample_drugs,
        )

    conn.commit()
    conn.close()
    print("Database initialized successfully")


def json_serializer(obj: Any) -> str:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def close_db_connection(conn: sqlite3.Connection) -> None:
    if conn:
        conn.close()
