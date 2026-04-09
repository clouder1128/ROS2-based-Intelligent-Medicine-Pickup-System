"""P3模块测试框架 - planner.py单元测试"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from planner import TodoManager, TodoTask, TaskStatus, TaskCategory
from task_storage import SQLiteStorage, FileStorage


class TestTodoTask:
    """TodoTask 数据类测试"""
    
    def test_create_task_with_defaults(self):
        """测试使用默认参数创建任务"""
        task = TodoTask(content="测试任务")
        
        assert task.content == "测试任务"
        assert task.priority == 3
        assert task.status == TaskStatus.PENDING.value
        assert task.category == TaskCategory.OTHER.value
        assert task.id != ""
        assert task.created_at is not None
    
    def test_task_validation_priority(self):
        """测试优先级验证"""
        with pytest.raises(ValueError):
            TodoTask(content="任务", priority=0)
        
        with pytest.raises(ValueError):
            TodoTask(content="任务", priority=6)
    
    def test_mark_completed(self):
        """测试标记任务为完成"""
        task = TodoTask(content="任务")
        task.mark_completed(notes="完成备注")
        
        assert task.status == TaskStatus.COMPLETED.value
        assert task.completed_at is not None
        assert task.notes == "完成备注"
    
    def test_mark_in_progress(self):
        """测试标记任务为进行中"""
        task = TodoTask(content="任务")
        task.mark_in_progress()
        
        assert task.status == TaskStatus.IN_PROGRESS.value
    
    def test_get_completion_time(self):
        """测试获取完成耗时"""
        task = TodoTask(content="任务")
        assert task.get_completion_time() is None
        
        task.mark_completed()
        completion_time = task.get_completion_time()
        assert completion_time is not None
        assert completion_time >= 0
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        original = TodoTask(
            content="测试任务",
            priority=5,
            category=TaskCategory.SYMPTOM.value,
            dependencies=["dep1", "dep2"]
        )
        
        original.mark_completed(notes="完成")
        
        # 序列化
        task_dict = original.to_dict()
        
        # 反序列化
        restored = TodoTask.from_dict(task_dict)
        
        assert restored.content == original.content
        assert restored.priority == original.priority
        assert restored.status == original.status
        assert restored.dependencies == original.dependencies
        assert restored.notes == original.notes


class TestTodoManager:
    """TodoManager 测试"""
    
    def test_init_without_storage(self):
        """测试初始化（无存储）"""
        manager = TodoManager()
        assert manager.storage is None
        assert len(manager.tasks) == 0
    
    def test_add_todo(self):
        """测试添加任务"""
        manager = TodoManager()
        task = manager.add_todo("测试任务", priority=4)
        
        assert task.content == "测试任务"
        assert task.priority == 4
        assert task.id in manager.tasks
    
    def test_add_todo_with_invalid_content(self):
        """测试添加任务时的内容验证"""
        manager = TodoManager()
        
        with pytest.raises(ValueError):
            manager.add_todo("")
        
        with pytest.raises(ValueError):
            manager.add_todo("   ")
    
    def test_get_todo_list(self):
        """测试获取任务列表"""
        manager = TodoManager()
        manager.add_todo("任务1", priority=3)
        manager.add_todo("任务2", priority=5)
        manager.add_todo("任务3", priority=1)
        
        # 获取全部任务
        all_tasks = manager.get_todo_list()
        assert len(all_tasks) == 3
        
        # 按优先级排序（降序）
        sorted_tasks = manager.get_todo_list(sort_by_priority=True, sort_ascending=False)
        assert sorted_tasks[0].priority == 5
        assert sorted_tasks[2].priority == 1
    
    def test_get_pending_tasks(self):
        """测试获取待处理任务"""
        manager = TodoManager()
        task1 = manager.add_todo("任务1", priority=3)
        task2 = manager.add_todo("任务2", priority=5)
        
        manager.mark_completed(task1.id)
        
        pending = manager.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].id == task2.id
    
    def test_get_high_priority_tasks(self):
        """测试获取高优先级任务"""
        manager = TodoManager()
        manager.add_todo("任务1", priority=3)
        manager.add_todo("任务2", priority=5)
        manager.add_todo("任务3", priority=4)
        
        high_priority = manager.get_high_priority_tasks(threshold=4)
        assert len(high_priority) == 2
    
    def test_update_todo(self):
        """测试更新任务"""
        manager = TodoManager()
        task = manager.add_todo("原始内容", priority=3)
        
        success = manager.update_todo(
            task.id,
            content="新内容",
            priority=5
        )
        
        assert success is True
        updated = manager.get_todo(task.id)
        assert updated.content == "新内容"
        assert updated.priority == 5
    
    def test_mark_completed(self):
        """测试标记任务完成"""
        manager = TodoManager()
        task = manager.add_todo("任务")
        
        success = manager.mark_completed(task.id, notes="完成备注")
        assert success is True
        
        completed = manager.get_todo(task.id)
        assert completed.status == TaskStatus.COMPLETED.value
        assert completed.notes == "完成备注"
    
    def test_delete_todo(self):
        """测试删除任务"""
        manager = TodoManager()
        task = manager.add_todo("任务")
        
        success = manager.delete_todo(task.id)
        assert success is True
        assert manager.get_todo(task.id) is None
    
    def test_clear_completed_tasks(self):
        """测试清理已完成任务"""
        manager = TodoManager()
        task1 = manager.add_todo("任务1")
        task2 = manager.add_todo("任务2")
        
        manager.mark_completed(task1.id)
        
        count = manager.clear_completed_tasks()
        assert count == 1
        assert len(manager.get_todo_list()) == 1
    
    def test_get_summary(self):
        """测试获取任务摘要"""
        manager = TodoManager()
        task1 = manager.add_todo("任务1")
        task2 = manager.add_todo("任务2")
        task3 = manager.add_todo("任务3")
        
        manager.mark_in_progress(task1.id)
        manager.mark_completed(task2.id)
        
        summary = manager.get_summary()
        assert summary["total"] == 3
        assert summary[TaskStatus.PENDING.value] == 1
        assert summary[TaskStatus.IN_PROGRESS.value] == 1
        assert summary[TaskStatus.COMPLETED.value] == 1
    
    def test_get_tasks_by_symptom(self):
        """测试按症状查询任务"""
        manager = TodoManager()
        task1 = manager.add_todo(
            "查询关于头痛的药物",
            related_symptoms=["头痛"]
        )
        task2 = manager.add_todo(
            "查询关于发烧的药物",
            related_symptoms=["发烧"]
        )
        
        headache_tasks = manager.get_tasks_by_symptom("头痛")
        assert len(headache_tasks) == 1
        assert headache_tasks[0].id == task1.id


class TestSQLiteStorage:
    """SQLiteStorage 测试"""
    
    @pytest.fixture
    def storage(self):
        """创建临时数据库"""
        storage = SQLiteStorage(":memory:")
        yield storage
        storage.close()
    
    def test_save_and_load_task(self, storage):
        """测试保存和加载任务"""
        task = TodoTask(
            id="test_1",
            content="测试任务",
            priority=5
        )
        
        assert storage.save_task(task) is True
        loaded = storage.load_task("test_1")
        
        assert loaded is not None
        assert loaded.content == "测试任务"
        assert loaded.priority == 5
    
    def test_load_all_tasks(self, storage):
        """测试加载所有任务"""
        task1 = TodoTask(id="1", content="任务1")
        task2 = TodoTask(id="2", content="任务2")
        
        storage.save_task(task1)
        storage.save_task(task2)
        
        all_tasks = storage.load_all_tasks()
        assert len(all_tasks) == 2
    
    def test_update_task(self, storage):
        """测试更新任务"""
        task = TodoTask(id="1", content="原始", priority=3)
        storage.save_task(task)
        
        success = storage.update_task("1", {
            "content": "更新后",
            "priority": 5
        })
        
        assert success is True
        updated = storage.load_task("1")
        assert updated.content == "更新后"
        assert updated.priority == 5
    
    def test_delete_task(self, storage):
        """测试删除任务"""
        task = TodoTask(id="1", content="任务")
        storage.save_task(task)
        
        assert storage.delete_task("1") is True
        assert storage.load_task("1") is None
    
    def test_delete_all_tasks_with_filter(self, storage):
        """测试按状态删除任务"""
        task1 = TodoTask(id="1", content="完成1", status=TaskStatus.COMPLETED.value)
        task2 = TodoTask(id="2", content="完成2", status=TaskStatus.COMPLETED.value)
        task3 = TodoTask(id="3", content="待处理", status=TaskStatus.PENDING.value)
        
        storage.save_task(task1)
        storage.save_task(task2)
        storage.save_task(task3)
        
        count = storage.delete_all_tasks(filter_by_status=TaskStatus.COMPLETED.value)
        assert count == 2
        
        remaining = storage.load_all_tasks()
        assert len(remaining) == 1
        assert remaining[0].id == "3"
    
    def test_get_tasks_by_status(self, storage):
        """测试按状态查询任务"""
        task1 = TodoTask(id="1", content="任务1", status=TaskStatus.PENDING.value)
        task2 = TodoTask(id="2", content="任务2", status=TaskStatus.IN_PROGRESS.value)
        
        storage.save_task(task1)
        storage.save_task(task2)
        
        pending = storage.get_tasks_by_status(TaskStatus.PENDING.value)
        assert len(pending) == 1
        assert pending[0].id == "1"


class TestFileStorage:
    """FileStorage 测试"""
    
    @pytest.fixture
    def storage(self):
        """创建临时存储目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            yield storage
    
    def test_save_and_load_task(self, storage):
        """测试保存和加载任务"""
        task = TodoTask(
            id="test_1",
            content="测试任务",
            priority=5
        )
        
        assert storage.save_task(task) is True
        loaded = storage.load_task("test_1")
        
        assert loaded is not None
        assert loaded.content == "测试任务"
        assert loaded.priority == 5
    
    def test_persistence(self):
        """测试持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 第一次保存
            storage1 = FileStorage(tmpdir)
            task = TodoTask(id="persistent", content="持久化任务")
            storage1.save_task(task)
            
            # 第二次加载
            storage2 = FileStorage(tmpdir)
            loaded = storage2.load_task("persistent")
            
            assert loaded is not None
            assert loaded.content == "持久化任务"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
