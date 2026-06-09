"""测试规划任务在 SQLite 与文件存储中的增删改查、筛选和异常处理。"""

from datetime import datetime

import pytest

from agent.planner.models import TodoTask
from agent.planner.storage import FileStorage, SQLiteStorage


def make_task(task_id="task-1", status="pending", priority=3):
    return TodoTask(
        id=task_id,
        content=f"content-{task_id}",
        status=status,
        priority=priority,
        category="query",
        related_symptoms=["headache"],
        dependencies=["dep-1"],
        notes="note",
    )


@pytest.mark.parametrize("storage_kind", ["sqlite", "file"])
def test_storage_crud_round_trip(tmp_path, storage_kind):
    if storage_kind == "sqlite":
        storage = SQLiteStorage(str(tmp_path / "tasks.db"))
    else:
        storage = FileStorage(str(tmp_path / "tasks"))

    task = make_task()
    assert storage.save_task(task) is True

    loaded = storage.load_task(task.id)
    assert loaded.content == task.content
    assert loaded.related_symptoms == ["headache"]
    assert loaded.dependencies == ["dep-1"]

    assert storage.update_task(
        task.id,
        {
            "content": "updated",
            "priority": 5,
            "updated_at": datetime.now(),
            "unknown": "ignored",
        },
    ) is True
    updated = storage.load_task(task.id)
    assert updated.content == "updated"
    assert updated.priority == 5

    assert len(storage.load_all_tasks()) == 1
    assert storage.delete_task(task.id) is True
    assert storage.delete_task(task.id) is False
    assert storage.load_task(task.id) is None

    if storage_kind == "sqlite":
        storage.close()


def test_sqlite_storage_filters_and_bulk_delete(tmp_path):
    storage = SQLiteStorage(str(tmp_path / "tasks.db"))
    pending = make_task("pending", priority=2)
    completed = make_task("completed", status="completed", priority=5)

    assert storage.save_task(pending) is True
    assert storage.save_task(completed) is True
    assert storage.save_task(make_task("pending", priority=4)) is True

    assert storage.load_task("missing") is None
    assert storage.update_task("missing", {"bad": "field"}) is False
    assert [task.id for task in storage.get_tasks_by_status("completed")] == [
        "completed"
    ]
    assert [task.priority for task in storage.get_tasks_by_priority(4)] == [5, 4]
    assert storage.delete_all_tasks("completed") == 1
    assert storage.delete_all_tasks() == 1
    storage.close()


def test_sqlite_storage_updates_existing_task(tmp_path):
    storage = SQLiteStorage(str(tmp_path / "tasks.db"))
    task = make_task()
    storage.save_task(task)
    task.content = "saved-again"
    task.status = "completed"
    task.completed_at = datetime.now()

    assert storage.save_task(task) is True
    loaded = storage.load_task(task.id)
    assert loaded.content == "saved-again"
    assert loaded.completed_at is not None
    storage.close()


def test_file_storage_filter_and_invalid_json(tmp_path):
    storage = FileStorage(str(tmp_path))
    storage.save_task(make_task("one"))
    storage.save_task(make_task("two", status="completed"))

    assert storage.delete_all_tasks("completed") == 1
    assert [task.id for task in storage.load_all_tasks()] == ["one"]

    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    assert storage.load_task("broken") is None
    assert storage.load_all_tasks() == []
    assert storage.delete_all_tasks() == 2
