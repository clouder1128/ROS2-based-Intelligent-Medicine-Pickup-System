"""
Main Flask Application Entry Point
Registers all controllers and starts the backend server
"""

import os
import sqlite3
import threading
import time
from datetime import date
from flask import Flask

# Configuration
from common.config import Config

# Controller imports
from api.health_controller import health_bp
from api.drug_controller import drug_bp
from api.order_controller import order_bp
from api.approval_controller import approval_bp

# Utility imports
from ros_integration.bridge import init_ros2, publish_expiry_removal
from common.utils.logger import setup_logger
from common.utils.database import get_db_connection

# ROS2集成模块（可选）
try:
    from ros_integration.health_monitor import HealthMonitor
    ROS2_INTEGRATION_AVAILABLE = True
except ImportError:
    ROS2_INTEGRATION_AVAILABLE = False
    HealthMonitor = None

# Start ROS2 initialization in background thread
_ros_thread = threading.Thread(target=init_ros2, daemon=True)
_ros_thread.start()

# Start health monitor if ROS2 integration is available
_health_monitor = None
if ROS2_INTEGRATION_AVAILABLE and HealthMonitor is not None:
    try:
        _health_monitor = HealthMonitor()
        _health_monitor.start()
        print("[Main] Health monitor started")
    except Exception as e:
        print(f"[Main] Failed to start health monitor: {e}")

# Flask app
app = Flask(__name__)

# CORS: Allow frontend cross-origin access
try:
    from flask_cors import CORS

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": Config.CORS_ORIGINS,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )
except ImportError:

    @app.after_request
    def add_cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = Config.CORS_ORIGINS
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return resp


# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(drug_bp)
app.register_blueprint(order_bp)
app.register_blueprint(approval_bp)

# Expiry sweep functionality
_expiry_sweep_lock = threading.Lock()
_expiry_bg_started = False
_expiry_bg_lock = threading.Lock()
EXPIRY_SWEEP_INTERVAL_SEC = int(os.environ.get("EXPIRY_SWEEP_INTERVAL_SEC", "3600"))


def _ensure_app_meta(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        )
    """)


def run_expiry_sweep() -> dict:
    if not os.path.exists(Config.DATABASE_PATH):
        return {"skipped": True, "reason": "no database"}

    today = date.today()
    today_s = today.isoformat()

    with _expiry_sweep_lock:
        conn = get_db_connection()
        try:
            _ensure_app_meta(conn)
            row = conn.execute(
                "SELECT v FROM app_meta WHERE k = 'expiry_sweep_date'"
            ).fetchone()
            last_s = row[0] if row else None

            if last_s == today_s:
                return {"skipped": True, "reason": "already_swept_today", "date": today_s}

            if last_s is None:
                conn.execute(
                    "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('expiry_sweep_date', ?)",
                    (today_s,),
                )
                conn.commit()
                return {"skipped": True, "reason": "legacy_baseline_no_init_meta", "date": today_s}

            try:
                last_d = date.fromisoformat(last_s)
            except ValueError:
                conn.execute(
                    "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('expiry_sweep_date', ?)",
                    (today_s,),
                )
                conn.commit()
                return {"skipped": True, "reason": "reset_invalid_last_date", "date": today_s}

            delta = (today - last_d).days
            if delta <= 0:
                return {"skipped": True, "reason": "no_new_day", "date": today_s}

            conn.execute(
                "UPDATE inventory SET expiry_date = expiry_date - ? WHERE expiry_date > 0",
                (delta,),
            )
            cur = conn.execute(
                """SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id
                   FROM inventory WHERE expiry_date <= 0 AND quantity > 0"""
            )
            expired_to_remove = [dict(r) for r in cur.fetchall()]

            cur = conn.execute(
                "UPDATE inventory SET quantity = 0 WHERE expiry_date <= 0"
            )
            cleared_rows = cur.rowcount

            conn.execute(
                "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('expiry_sweep_date', ?)",
                (today_s,),
            )
            conn.commit()

            ros_n = 0
            for drug in expired_to_remove:
                publish_expiry_removal(drug, int(drug["quantity"]))
                ros_n += 1

            return {
                "success": True,
                "ok": True,
                "date": today_s,
                "days_applied": delta,
                "expired_rows_cleared_qty": cleared_rows,
                "expiry_ros_published": ros_n,
            }
        finally:
            conn.close()


def _expiry_sweep_loop():
    while True:
        try:
            summary = run_expiry_sweep()
            if summary.get("ok"):
                print(f"[expiry] 清扫完成: {summary}")
            elif not summary.get("skipped"):
                print(f"[expiry] 清扫结果: {summary}")
        except Exception as e:
            print(f"[expiry] 清扫异常: {e}")
        time.sleep(EXPIRY_SWEEP_INTERVAL_SEC)


def _boot_expiry_worker_once():
    global _expiry_bg_started
    with _expiry_bg_lock:
        if _expiry_bg_started:
            return
        _expiry_bg_started = True
    threading.Thread(target=_expiry_sweep_loop, daemon=True).start()


if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    _boot_expiry_worker_once()


if __name__ == "__main__":
    if not os.path.exists(Config.DATABASE_PATH):
        print("请先运行: python3 init_db.py")
        exit(1)
    _debug = True
    _use_reloader = _debug
    if not (_debug and _use_reloader):
        _boot_expiry_worker_once()

    app.run(
        host=Config.HOST, port=Config.PORT, debug=_debug, use_reloader=_use_reloader
    )
