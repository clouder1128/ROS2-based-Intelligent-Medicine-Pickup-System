"""TodoManager / TodoTask / TaskStorage 纯逻辑单元测试

无外部依赖：纯内存任务管理。
TodoTask.status 为字符串（TaskStatus.value），比较时需用 .value。
"""

from agent.planner.models import TodoManager, TodoTask, TaskStatus, TaskCategory


class TestTaskStatus:
    def test_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"


class TestTaskCategory:
    def test_category_values(self):
        assert TaskCategory.SYMPTOM.value == "symptom"
        assert TaskCategory.QUERY.value == "query"
        assert TaskCategory.CHECK.value == "check"
        assert TaskCategory.DOSAGE.value == "dosage"
        assert TaskCategory.APPROVAL.value == "approval"


class TestTodoTask:
    def test_default_creation(self):
        task = TodoTask(content="测试任务")
        assert task.content == "测试任务"
        assert task.priority == 3
        assert task.status == TaskStatus.PENDING.value
        assert task.category == TaskCategory.OTHER.value
        assert task.id is not None

    def test_custom_creation(self):
        task = TodoTask(content="高优先级任务", priority=1, category=TaskCategory.APPROVAL.value)
        assert task.priority == 1
        assert task.category == TaskCategory.APPROVAL.value

    def test_mark_completed(self):
        task = TodoTask(content="测试")
        task.mark_completed()
        assert task.status == TaskStatus.COMPLETED.value
        assert task.completed_at is not None

    def test_mark_in_progress(self):
        task = TodoTask(content="测试")
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS.value

    def test_mark_blocked(self):
        task = TodoTask(content="测试")
        task.mark_blocked()
        assert task.status == TaskStatus.BLOCKED.value

    def test_is_completed(self):
        task = TodoTask(content="测试")
        assert task.is_completed() is False
        task.mark_completed()
        assert task.is_completed() is True

    def test_get_age(self):
        task = TodoTask(content="测试")
        age = task.get_age()
        assert age >= 0

    def test_to_dict(self):
        task = TodoTask(content="测试任务", priority=2, category=TaskCategory.QUERY.value)
        d = task.to_dict()
        assert d["content"] == "测试任务"
        assert d["priority"] == 2
        assert d["category"] == "query"

    def test_from_dict(self):
        task = TodoTask(content="测试任务", priority=1)
        d = task.to_dict()
        restored = TodoTask.from_dict(d)
        assert restored.content == task.content
        assert restored.priority == task.priority
        assert restored.id == task.id


class TestTodoManager:
    def test_add_and_get_todo(self):
        mgr = TodoManager()
        task = mgr.add_todo("测试任务")
        tid = task.id
        retrieved = mgr.get_todo(tid)
        assert retrieved is not None
        assert retrieved.content == "测试任务"

    def test_get_nonexistent_returns_none(self):
        mgr = TodoManager()
        assert mgr.get_todo("nonexistent") is None

    def test_get_todo_list(self):
        mgr = TodoManager()
        mgr.add_todo("任务1")
        mgr.add_todo("任务2")
        assert len(mgr.get_todo_list()) == 2

    def test_get_pending_tasks(self):
        mgr = TodoManager()
        mgr.add_todo("待办")
        t2 = mgr.add_todo("已完成")
        t2.mark_completed()
        pending = mgr.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].content == "待办"

    def test_get_high_priority_tasks(self):
        mgr = TodoManager()
        mgr.add_todo("普通", priority=3)
        high = mgr.add_todo("高优先级", priority=4)
        high_list = mgr.get_high_priority_tasks()
        assert high in high_list

    def test_get_tasks_by_category(self):
        mgr = TodoManager()
        mgr.add_todo("查询药品", category=TaskCategory.QUERY.value)
        mgr.add_todo("检查过敏", category=TaskCategory.CHECK.value)
        queries = mgr.get_tasks_by_category(TaskCategory.QUERY.value)
        assert len(queries) == 1

    def test_update_todo(self):
        mgr = TodoManager()
        task = mgr.add_todo("旧内容")
        mgr.update_todo(task.id, content="新内容", priority=1)
        updated = mgr.get_todo(task.id)
        assert updated.content == "新内容"
        assert updated.priority == 1

    def test_manager_mark_completed(self):
        mgr = TodoManager()
        task = mgr.add_todo("测试")
        mgr.mark_completed(task.id)
        assert mgr.get_todo(task.id).status == TaskStatus.COMPLETED.value

    def test_manager_mark_in_progress(self):
        mgr = TodoManager()
        task = mgr.add_todo("测试")
        mgr.mark_in_progress(task.id)
        assert mgr.get_todo(task.id).status == TaskStatus.IN_PROGRESS.value

    def test_delete_todo(self):
        mgr = TodoManager()
        task = mgr.add_todo("测试")
        mgr.delete_todo(task.id)
        assert mgr.get_todo(task.id) is None

    def test_clear_completed_tasks(self):
        mgr = TodoManager()
        t1 = mgr.add_todo("待办")
        t2 = mgr.add_todo("已完成")
        t2.mark_completed()
        mgr.clear_completed_tasks()
        assert mgr.get_todo(t1.id) is not None
        assert mgr.get_todo(t2.id) is None

    def test_get_summary(self):
        mgr = TodoManager()
        mgr.add_todo("任务1", priority=1)
        mgr.add_todo("任务2", priority=3)
        summary = mgr.get_summary()
        assert summary["total"] == 2
        assert summary["pending"] == 2
