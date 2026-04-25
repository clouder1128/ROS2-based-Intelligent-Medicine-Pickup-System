"""任务存储模块 - 支持SQLite和文件存储的持久化存储层"""

import logging
import sqlite3
import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """存储操作异常"""
    pass


class TaskStorage(ABC):
    """任务存储抽象基类"""

    @abstractmethod
    def save_task(self, task: "TodoTask") -> bool:
        pass

    @abstractmethod
    def load_task(self, task_id: str) -> Optional["TodoTask"]:
        pass

    @abstractmethod
    def load_all_tasks(self) -> List["TodoTask"]:
        pass

    @abstractmethod
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        pass

    @abstractmethod
    def delete_all_tasks(self, filter_by_status: Optional[str] = None) -> int:
        pass


class SQLiteStorage(TaskStorage):
    """基于SQLite的任务持久化存储"""

    def __init__(self, db_path: str = "./tasks.db"):
        self.db_path = db_path
        self.connection = None
        self._connect()
        self._create_schema()
        logger.info(f"SQLiteStorage 初始化: {db_path}")

    def _connect(self) -> None:
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            logger.error(f"无法连接到数据库 {self.db_path}: {e}")
            raise StorageError(f"数据库连接失败: {e}")

    def _create_schema(self) -> None:
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority INTEGER NOT NULL DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
                    category TEXT DEFAULT 'other',
                    related_symptoms TEXT,
                    dependencies TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    notes TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON tasks(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_priority
                ON tasks(priority)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_category
                ON tasks(category)
            """)

            self.connection.commit()
            logger.debug("数据库表结构创建/验证成功")

        except sqlite3.Error as e:
            logger.error(f"创建表结构失败: {e}")
            raise StorageError(f"表结构创建失败: {e}")

    def save_task(self, task: "TodoTask") -> bool:
        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT id FROM tasks WHERE id = ?", (task.id,))
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute("""
                    UPDATE tasks
                    SET content = ?, status = ?, priority = ?, category = ?,
                        related_symptoms = ?, dependencies = ?,
                        updated_at = ?, completed_at = ?, notes = ?
                    WHERE id = ?
                """, (
                    task.content,
                    task.status,
                    task.priority,
                    task.category,
                    json.dumps(task.related_symptoms),
                    json.dumps(task.dependencies),
                    task.updated_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.notes,
                    task.id
                ))
                logger.debug(f"任务更新到数据库: {task.id}")
            else:
                cursor.execute("""
                    INSERT INTO tasks
                    (id, content, status, priority, category,
                     related_symptoms, dependencies, created_at, updated_at,
                     completed_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.id,
                    task.content,
                    task.status,
                    task.priority,
                    task.category,
                    json.dumps(task.related_symptoms),
                    json.dumps(task.dependencies),
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.notes
                ))
                logger.debug(f"任务保存到数据库: {task.id}")

            self.connection.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"保存任务失败: {e}")
            self.connection.rollback()
            return False

    def load_task(self, task_id: str) -> Optional["TodoTask"]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_task(dict(row))
            return None

        except sqlite3.Error as e:
            logger.error(f"加载任务失败: {e}")
            return None

    def load_all_tasks(self) -> List["TodoTask"]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            rows = cursor.fetchall()

            tasks = [self._row_to_task(dict(row)) for row in rows]
            logger.debug(f"从数据库加载 {len(tasks)} 个任务")
            return tasks

        except sqlite3.Error as e:
            logger.error(f"加载任务列表失败: {e}")
            return []

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        try:
            valid_fields = {
                'content', 'status', 'priority', 'category',
                'related_symptoms', 'dependencies',
                'updated_at', 'completed_at', 'notes'
            }

            update_fields = {k: v for k, v in updates.items() if k in valid_fields}
            if not update_fields:
                return False

            if 'related_symptoms' in update_fields:
                update_fields['related_symptoms'] = json.dumps(update_fields['related_symptoms'])
            if 'dependencies' in update_fields:
                update_fields['dependencies'] = json.dumps(update_fields['dependencies'])

            if 'updated_at' in update_fields and isinstance(update_fields['updated_at'], datetime):
                update_fields['updated_at'] = update_fields['updated_at'].isoformat()
            if 'completed_at' in update_fields and isinstance(update_fields['completed_at'], datetime):
                update_fields['completed_at'] = update_fields['completed_at'].isoformat()

            cursor = self.connection.cursor()

            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values()) + [task_id]

            cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            self.connection.commit()

            logger.debug(f"任务字段更新: {task_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"更新任务失败: {e}")
            self.connection.rollback()
            return False

    def delete_task(self, task_id: str) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.connection.commit()

            if cursor.rowcount > 0:
                logger.debug(f"任务删除: {task_id}")
                return True
            return False

        except sqlite3.Error as e:
            logger.error(f"删除任务失败: {e}")
            self.connection.rollback()
            return False

    def delete_all_tasks(self, filter_by_status: Optional[str] = None) -> int:
        try:
            cursor = self.connection.cursor()

            if filter_by_status:
                cursor.execute("DELETE FROM tasks WHERE status = ?", (filter_by_status,))
            else:
                cursor.execute("DELETE FROM tasks")

            self.connection.commit()
            count = cursor.rowcount
            logger.info(f"删除 {count} 个任务 (状态过滤: {filter_by_status})")
            return count

        except sqlite3.Error as e:
            logger.error(f"批量删除任务失败: {e}")
            self.connection.rollback()
            return 0

    def get_tasks_by_status(self, status: str) -> List["TodoTask"]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC",
                (status,)
            )
            rows = cursor.fetchall()
            return [self._row_to_task(dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"按状态查询任务失败: {e}")
            return []

    def get_tasks_by_priority(self, min_priority: int) -> List["TodoTask"]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE priority >= ? ORDER BY priority DESC",
                (min_priority,)
            )
            rows = cursor.fetchall()
            return [self._row_to_task(dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"按优先级查询任务失败: {e}")
            return []

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")

    @staticmethod
    def _row_to_task(row: Dict[str, Any]) -> "TodoTask":
        from .models import TodoTask

        return TodoTask(
            id=row['id'],
            content=row['content'],
            status=row['status'],
            priority=row['priority'],
            category=row['category'],
            related_symptoms=json.loads(row['related_symptoms']) if row['related_symptoms'] else [],
            dependencies=json.loads(row['dependencies']) if row['dependencies'] else [],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            notes=row['notes']
        )


class FileStorage(TaskStorage):
    """基于JSON文件的任务存储"""

    def __init__(self, data_dir: str = "./tasks_data"):
        self.data_dir = Path(data_dir)
        self._ensure_directory()
        logger.info(f"FileStorage 初始化: {data_dir}")

    def save_task(self, task: "TodoTask") -> bool:
        try:
            file_path = self._task_file_path(task.id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug(f"任务保存到文件: {task.id}")
            return True

        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"保存任务失败: {e}")
            return False

    def load_task(self, task_id: str) -> Optional["TodoTask"]:
        try:
            file_path = self._task_file_path(task_id)
            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            from .models import TodoTask
            return TodoTask.from_dict(data)

        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"加载任务失败: {e}")
            return None

    def load_all_tasks(self) -> List["TodoTask"]:
        try:
            tasks = []
            for file_path in self._get_all_task_files():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                from .models import TodoTask
                tasks.append(TodoTask.from_dict(data))

            logger.debug(f"从文件加载 {len(tasks)} 个任务")
            return tasks

        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"加载任务列表失败: {e}")
            return []

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        try:
            task = self.load_task(task_id)
            if not task:
                return False

            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            return self.save_task(task)

        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        try:
            file_path = self._task_file_path(task_id)
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"任务删除: {task_id}")
                return True
            return False

        except IOError as e:
            logger.error(f"删除任务失败: {e}")
            return False

    def delete_all_tasks(self, filter_by_status: Optional[str] = None) -> int:
        try:
            count = 0
            for file_path in self._get_all_task_files():
                if filter_by_status:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data.get('status') != filter_by_status:
                        continue

                file_path.unlink()
                count += 1

            logger.info(f"删除 {count} 个任务 (状态过滤: {filter_by_status})")
            return count

        except Exception as e:
            logger.error(f"批量删除任务失败: {e}")
            return 0

    def _ensure_directory(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _task_file_path(self, task_id: str) -> Path:
        return self.data_dir / f"{task_id}.json"

    def _get_all_task_files(self) -> List[Path]:
        return list(self.data_dir.glob("*.json"))
