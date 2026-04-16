"""规划器模块 - TodoWrite待办项目管理系统"""

import logging
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 待处理
    IN_PROGRESS = "in_progress"   # 进行中
    COMPLETED = "completed"       # 已完成
    BLOCKED = "blocked"           # 被阻止


class TaskCategory(Enum):
    """任务分类枚举"""
    SYMPTOM = "symptom"           # 症状相关
    QUERY = "query"               # 查询相关
    CHECK = "check"               # 检查相关
    DOSAGE = "dosage"             # 剂量计算
    APPROVAL = "approval"         # 审批相关
    OTHER = "other"               # 其他


@dataclass
class TodoTask:
    """待办任务数据类"""
    
    content: str                              # 任务内容
    priority: int = 3                        # 优先级 1-5（5最高）
    status: str = TaskStatus.PENDING.value   # 任务状态
    category: str = TaskCategory.OTHER.value # 任务分类
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    related_symptoms: List[str] = field(default_factory=list)  # 关联的症状列表
    dependencies: List[str] = field(default_factory=list)      # 依赖的任务ID
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None              # 完成时的备注
    
    def __post_init__(self):
        """初始化后验证数据"""
        if not 1 <= self.priority <= 5:
            raise ValueError(f"优先级必须在1-5之间，当前值: {self.priority}")
        
        # 确保status和status的值有效
        valid_statuses = {s.value for s in TaskStatus}
        if self.status not in valid_statuses:
            raise ValueError(f"无效的任务状态: {self.status}")
    
    def mark_in_progress(self) -> None:
        """标记为进行中"""
        self.status = TaskStatus.IN_PROGRESS.value
        self.updated_at = datetime.now()
    
    def mark_completed(self, notes: Optional[str] = None) -> None:
        """标记为已完成"""
        self.status = TaskStatus.COMPLETED.value
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        if notes:
            self.notes = notes
    
    def mark_blocked(self) -> None:
        """标记为被阻止"""
        self.status = TaskStatus.BLOCKED.value
        self.updated_at = datetime.now()
    
    def mark_pending(self) -> None:
        """标记为待处理"""
        self.status = TaskStatus.PENDING.value
        self.updated_at = datetime.now()
    
    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status == TaskStatus.COMPLETED.value
    
    def is_pending(self) -> bool:
        """检查是否待处理"""
        return self.status == TaskStatus.PENDING.value
    
    def get_age(self) -> float:
        """获取任务年龄（秒）"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def get_completion_time(self) -> Optional[float]:
        """获取完成耗时（秒），未完成则返回None"""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        # 转换datetime对象为ISO格式字符串
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoTask":
        """从字典创建任务"""
        # 处理datetime字段
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('completed_at') and isinstance(data['completed_at'], str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        return cls(**data)


class TodoManager:
    """待办项目经理 - 管理医疗咨询过程中的任务"""
    
    def __init__(self, storage=None):
        """
        初始化规划器
        
        Args:
            storage: TaskStorage实例，支持SQLite和文件存储
                    如果为None，则使用内存存储
        """
        self.storage = storage
        self.tasks: Dict[str, TodoTask] = {}  # 内存缓存
        
        # 如果有存储，加载现有任务
        if self.storage:
            self._load_from_storage()
        
        logger.info("TodoManager 初始化成功")
    
    def add_todo(
        self,
        content: str,
        priority: int = 3,
        category: str = TaskCategory.OTHER.value,
        related_symptoms: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> TodoTask:
        """
        添加新任务
        
        Args:
            content: 任务内容
            priority: 优先级 1-5
            category: 任务分类
            related_symptoms: 关联的症状列表
            dependencies: 依赖的任务ID列表
        
        Returns:
            TodoTask: 新创建的任务
        
        Raises:
            ValueError: 当优先级无效或内容为空时
        """
        if not content or not content.strip():
            raise ValueError("任务内容不能为空")
        
        task = TodoTask(
            content=content,
            priority=priority,
            category=category,
            related_symptoms=related_symptoms or [],
            dependencies=dependencies or []
        )
        
        self.tasks[task.id] = task
        
        # 保存到存储
        if self.storage:
            self.storage.save_task(task)
        
        logger.info(f"任务添加: {task.id} - {content}")
        return task
    
    def get_todo(self, task_id: str) -> Optional[TodoTask]:
        """获取特定任务"""
        return self.tasks.get(task_id)
    
    def get_todo_list(
        self,
        filter_by_status: Optional[str] = None,
        sort_by_priority: bool = True,
        sort_ascending: bool = False
    ) -> List[TodoTask]:
        """
        获取任务列表
        
        Args:
            filter_by_status: 按状态筛选（可选）
            sort_by_priority: 是否按优先级排序
            sort_ascending: 是否按升序排序（False=降序/高优先级优先）
        
        Returns:
            List[TodoTask]: 任务列表
        """
        tasks = list(self.tasks.values())
        
        # 按状态筛选
        if filter_by_status:
            tasks = [t for t in tasks if t.status == filter_by_status]
        
        # 按优先级排序
        if sort_by_priority:
            tasks.sort(key=lambda t: t.priority, reverse=not sort_ascending)
        
        return tasks
    
    def get_pending_tasks(self) -> List[TodoTask]:
        """获取所有待处理任务（按优先级降序）"""
        return self.get_todo_list(
            filter_by_status=TaskStatus.PENDING.value,
            sort_by_priority=True,
            sort_ascending=False
        )
    
    def get_high_priority_tasks(self, threshold: int = 4) -> List[TodoTask]:
        """
        获取高优先级任务
        
        Args:
            threshold: 优先级阈值（>=此值的任务）
        
        Returns:
            List[TodoTask]: 高优先级任务列表
        """
        return [t for t in self.tasks.values() if t.priority >= threshold]
    
    def get_tasks_by_category(self, category: str) -> List[TodoTask]:
        """按分类获取任务"""
        return [t for t in self.tasks.values() if t.category == category]
    
    def get_tasks_by_symptom(self, symptom: str) -> List[TodoTask]:
        """获取与特定症状相关的任务"""
        return [
            t for t in self.tasks.values()
            if symptom in t.related_symptoms
        ]
    
    def update_todo(
        self,
        task_id: str,
        content: Optional[str] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            content: 新的任务内容
            priority: 新的优先级
            status: 新的状态
            category: 新的分类
            notes: 备注
        
        Returns:
            bool: 是否更新成功
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        if content is not None and content.strip():
            task.content = content
        
        if priority is not None:
            if not 1 <= priority <= 5:
                logger.error(f"无效的优先级: {priority}")
                return False
            task.priority = priority
        
        if status is not None:
            valid_statuses = {s.value for s in TaskStatus}
            if status not in valid_statuses:
                logger.error(f"无效的状态: {status}")
                return False
            task.status = status
        
        if category is not None:
            task.category = category
        
        if notes is not None:
            task.notes = notes
        
        task.updated_at = datetime.now()
        
        # 保存到存储
        if self.storage:
            self.storage.update_task(task_id, task.to_dict())
        
        logger.info(f"任务更新: {task_id}")
        return True
    
    def mark_completed(self, task_id: str, notes: Optional[str] = None) -> bool:
        """
        标记任务为已完成
        
        Args:
            task_id: 任务ID
            notes: 完成备注
        
        Returns:
            bool: 是否标记成功
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        task.mark_completed(notes)
        
        # 保存到存储
        if self.storage:
            self.storage.update_task(task_id, task.to_dict())
        
        logger.info(f"任务完成: {task_id}")
        return True
    
    def mark_in_progress(self, task_id: str) -> bool:
        """标记任务为进行中"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.mark_in_progress()
        if self.storage:
            self.storage.update_task(task_id, task.to_dict())
        
        return True
    
    def delete_todo(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            bool: 是否删除成功
        """
        if task_id not in self.tasks:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        del self.tasks[task_id]
        
        # 删除存储中的任务
        if self.storage:
            self.storage.delete_task(task_id)
        
        logger.info(f"任务删除: {task_id}")
        return True
    
    def clear_completed_tasks(self) -> int:
        """
        清理已完成的任务
        
        Returns:
            int: 清理的任务数量
        """
        completed_ids = [
            task_id for task_id, task in self.tasks.items()
            if task.is_completed()
        ]
        
        for task_id in completed_ids:
            self.delete_todo(task_id)
        
        logger.info(f"清理了 {len(completed_ids)} 个已完成的任务")
        return len(completed_ids)
    
    def get_summary(self) -> Dict[str, int]:
        """
        获取任务摘要统计
        
        Returns:
            Dict[str, int]: 各状态任务数量统计
        """
        summary = {
            "total": len(self.tasks),
            TaskStatus.PENDING.value: 0,
            TaskStatus.IN_PROGRESS.value: 0,
            TaskStatus.COMPLETED.value: 0,
            TaskStatus.BLOCKED.value: 0
        }
        
        for task in self.tasks.values():
            summary[task.status] += 1
        
        return summary
    
    def _load_from_storage(self) -> None:
        """从存储加载所有任务"""
        if not self.storage:
            return
        
        tasks = self.storage.load_all_tasks()
        self.tasks = {task.id: task for task in tasks}
        logger.info(f"从存储加载了 {len(tasks)} 个任务")
