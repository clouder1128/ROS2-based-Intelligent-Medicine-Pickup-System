# P3 实现指南：规划器、任务持久化、症状提取子代理

## 📋 概述

P3 模块负责实现三个关键功能：
1. **planner.py** - TodoWrite规划器，管理待办任务清单
2. **task_storage.py** - 任务持久化存储，支持SQLite和JSON
3. **subagents/symptom_extractor.py** - 症状提取子代理，从用户输入提取结构化症状信息

这些模块与P1的MedicalAgent无缝集成，支持整个医疗咨询工作流。

---

## 🎯 架构设计

### 数据流

```
用户输入
   ↓
症状提取子代理 (symptom_extractor.py)
   ├─ 识别症状、体征、患者信息
   └─ 返回 StructuredSymptoms
   ↓
规划器 (planner.py)
   ├─ 分析症状生成待办任务列表
   ├─ 优先级排序
   └─ 返回 TodoTask 列表
   ↓
任务持久化 (task_storage.py)
   ├─ 保存任务到数据库/文件
   ├─ 支持查询、更新、删除
   └─ 支持批量操作
   ↓
MedicalAgent (core/agent.py)
   └─ 执行任务，调用工具系统
```

### 类关系图

```
TodoManager
├── storage: TaskStorage
├── tasks: Dict[str, TodoTask]
└── Methods: add_todo, get_todo_list, update_todo, mark_completed, ...

TaskStorage (Abstract)
├── SQLiteStorage
└── FileStorage

TodoTask
├── id: str
├── content: str
├── status: str (pending, in_progress, completed)
├── priority: int (1-5)
├── created_at: datetime
└── completed_at: Optional[datetime]

StructuredSymptoms
├── chief_complaint: str
├── symptoms: List[str]
├── signs: Dict[str, Any]
├── patient_info: PatientInfo
└── medical_history: Optional[Dict[str, Any]]

PatientInfo
├── age: Optional[int]
├── weight: Optional[float]
├── gender: Optional[str]
└── allergies: Optional[List[str]]
```

---

## 📁 文件结构

```
P1/
├── planner.py                     # 规划器 (需创建)
├── task_storage.py                # 任务存储 (需创建)
├── subagents/                     # 子代理目录 (需创建)
│   ├── __init__.py
│   └── symptom_extractor.py       # 症状提取子代理 (需创建)
├── core/
│   ├── agent.py                   # 已集成P3接口
│   └── workflows.py
├── utils/
│   └── json_tools.py              # 辅助工具
└── tests/
    ├── test_planner.py            # 规划器测试 (可新增)
    ├── test_task_storage.py       # 存储测试 (可新增)
    └── test_symptom_extractor.py  # 子代理测试 (可新增)
```

---

## 🛠️ 实现方案

### 1️⃣ planner.py - 规划器

**职责**：
- 管理待办任务清单（TodoWrite风格）
- 任务优先级排序
- 任务状态转换管理
- 与任务存储交互

**关键类**：

```python
class TodoTask:
    """待办任务数据类"""
    - id: str                          # 唯一标识
    - content: str                     # 任务内容
    - status: str                      # 待决/进行中/完成
    - priority: int                    # 优先级 1-5
    - category: str                    # 分类 (症状, 查询, 检查等)
    - created_at: datetime
    - completed_at: Optional[datetime]
    - related_symptoms: List[str]      # 关联症状
    - dependencies: List[str]          # 依赖的任务ID

class TodoManager:
    """待办项目经理"""
    Methods:
    - add_todo(content, priority, category, dependencies=[]) -> TodoTask
    - get_todo_list(filter_by_status=None, sort_by_priority=True) -> List[TodoTask]
    - get_todo(task_id) -> Optional[TodoTask]
    - update_todo(task_id, content=None, priority=None, status=None) -> bool
    - mark_completed(task_id, notes=None) -> bool
    - get_pending_tasks() -> List[TodoTask]
    - get_high_priority_tasks(threshold=4) -> List[TodoTask]
    - clear_completed_tasks() -> int
    - get_summary() -> Dict[str, int]
```

**示例使用**：

```python
from planner import TodoManager

# 初始化
planner = TodoManager(storage="sqlite")  # 或 "file"

# 添加任务
task1 = planner.add_todo(
    content="询问患者的过敏史",
    priority=5,
    category="symptom"
)

task2 = planner.add_todo(
    content="查询建议的药物",
    priority=4,
    category="query",
    dependencies=[task1.id]
)

# 查看待办项
pending = planner.get_pending_tasks()
print(f"共有 {len(pending)} 个待办项")

# 标记完成
planner.mark_completed(task1.id, notes="患者无过敏史")

# 获取摘要
summary = planner.get_summary()
# {'total': 2, 'pending': 1, 'completed': 1}
```

---

### 2️⃣ task_storage.py - 任务持久化

**职责**：
- 抽象存储接口（Abstract Base Class）
- SQLite实现
- 文件系统实现
- CRUD操作和批量操作

**关键类**：

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class TaskStorage(ABC):
    """任务存储抽象基类"""
    
    @abstractmethod
    def save_task(self, task: TodoTask) -> bool:
        """保存单个任务"""
        pass
    
    @abstractmethod
    def load_task(self, task_id: str) -> Optional[TodoTask]:
        """加载单个任务"""
        pass
    
    @abstractmethod
    def load_all_tasks(self) -> List[TodoTask]:
        """加载所有任务"""
        pass
    
    @abstractmethod
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新任务"""
        pass
    
    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        pass
    
    @abstractmethod
    def delete_all_tasks(self, filter_by_status: Optional[str] = None) -> int:
        """批量删除任务"""
        pass


class SQLiteStorage(TaskStorage):
    """基于SQLite的持久化存储"""
    
    Methods:
    - __init__(db_path: str = "./tasks.db")
    - save_task(task) -> bool                  # 保存/更新任务
    - load_task(task_id) -> Optional[TodoTask]
    - load_all_tasks() -> List[TodoTask]
    - update_task(task_id, updates) -> bool
    - delete_task(task_id) -> bool
    - delete_all_tasks(filter_by_status=None) -> int
    - get_tasks_by_status(status: str) -> List[TodoTask]
    - get_tasks_by_priority(min_priority: int) -> List[TodoTask]
    - _create_schema()                        # 初始化数据库表
    - _task_to_row(task) -> tuple
    - _row_to_task(row) -> TodoTask
    - close()


class FileStorage(TaskStorage):
    """基于JSON文件的存储"""
    
    Methods:
    - __init__(data_dir: str = "./tasks_data")
    - save_task(task) -> bool
    - load_task(task_id) -> Optional[TodoTask]
    - load_all_tasks() -> List[TodoTask]
    - update_task(task_id, updates) -> bool
    - delete_task(task_id) -> bool
    - delete_all_tasks(filter_by_status=None) -> int
    - _ensure_directory()                     # 确保目录存在
    - _task_file_path(task_id) -> str
    - _get_all_task_files() -> List[str]
    - _load_from_file(file_path) -> Optional[dict]
    - _save_to_file(data: dict, file_path: str) -> bool
```

**数据库Schema (SQLite)**：

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    status TEXT NOT NULL,          -- pending, in_progress, completed
    priority INTEGER CHECK(priority BETWEEN 1 AND 5),
    category TEXT,                 -- symptom, query, check, etc.
    related_symptoms TEXT,         -- JSON array stored as string
    dependencies TEXT,             -- JSON array stored as string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_category ON tasks(category);
```

**使用示例**：

```python
from task_storage import SQLiteStorage, FileStorage
from planner import TodoTask

# SQLite存储
storage = SQLiteStorage("./medical_tasks.db")

# 保存任务
task = TodoTask(
    id="task_001",
    content="询问患者症状",
    status="pending",
    priority=5,
    category="symptom"
)
storage.save_task(task)

# 加载任务
loaded = storage.load_task("task_001")

# 查询特定状态的任务
pending_tasks = storage.get_tasks_by_status("pending")

# 更新任务
storage.update_task("task_001", {
    "status": "completed",
    "notes": "已询问，患者描述为头晕"
})

# 清理已完成的任务
count = storage.delete_all_tasks(filter_by_status="completed")
print(f"删除了 {count} 个已完成的任务")
```

---

### 3️⃣ subagents/symptom_extractor.py - 症状提取子代理

**职责**：
- 从自然语言用户输入提取结构化症状信息
- 识别患者基本信息（年龄、性别、体重）
- 识别症状、体征和既往史
- 使用LLM进行智能提取

**关键类和函数**：

```python
@dataclass
class PatientInfo:
    """患者基本信息"""
    age: Optional[int] = None
    weight: Optional[float] = None      # kg
    gender: Optional[str] = None         # M/F
    allergies: Optional[List[str]] = None


@dataclass
class StructuredSymptoms:
    """结构化症状信息"""
    chief_complaint: str                 # 主诉
    symptoms: List[str]                 # 症状列表
    signs: Dict[str, Any]               # 体征 {name: value, ...}
    patient_info: PatientInfo           # 患者信息
    medical_history: Optional[Dict[str, Any]] = None  # 既往史


class SymptomExtractor:
    """症状提取核心类"""
    
    Methods:
    - __init__(llm_client: LLMClient = None, use_llm: bool = True)
    - extract(user_input: str) -> StructuredSymptoms
    - extract_chief_complaint(text: str) -> str
    - extract_patient_info(text: str) -> PatientInfo
    - extract_symptoms(text: str) -> List[str]
    - extract_signs(text: str) -> Dict[str, Any]
    - extract_medical_history(text: str) -> Optional[Dict[str, Any]]
    - validate_symptoms(symptoms: StructuredSymptoms) -> Tuple[bool, Optional[str]]


# 便捷函数
async def extract_symptoms(user_input: str) -> StructuredSymptoms:
    """
    从用户输入提取症状信息（异步）
    
    Args:
        user_input: 用户输入的症状描述
    
    Returns:
        StructuredSymptoms: 结构化症状信息
    
    Raises:
        ExtractionError: 提取失败时抛出
    """
    pass


def extract_symptoms_sync(user_input: str) -> StructuredSymptoms:
    """同步版本的症状提取"""
    pass
```

**LLM提示词设计**：

```python
SYMPTOM_EXTRACTION_PROMPT = """
You are a medical information extraction specialist. Your task is to analyze patient descriptions and extract structured medical information.

Given the patient's description, extract and structure the following information:

1. Chief Complaint (主诉): The main reason for the visit
2. Symptoms (症状): List of reported symptoms
3. Signs (体征): Objective physical findings
4. Patient Info (患者信息): Age, weight, gender, allergies
5. Medical History (既往史): Relevant past medical history

Return a JSON object with this structure:
{
    "chief_complaint": "string",
    "symptoms": ["symptom1", "symptom2", ...],
    "signs": {
        "symptom_name": "value",
        ...
    },
    "patient_info": {
        "age": integer or null,
        "weight": float or null,
        "gender": "M" or "F" or null,
        "allergies": ["allergy1", ...] or null
    },
    "medical_history": {
        "condition": "description",
        ...
    } or null
}

Be systematic and extract all available information.
"""
```

**使用示例**：

```python
from subagents.symptom_extractor import extract_symptoms, StructuredSymptoms

# 异步使用
import asyncio

async def main():
    user_input = "我是一个30岁的女性，体重60kg，最近头痛厉害，还有点发烧，对阿司匹林过敏"
    
    symptoms = await extract_symptoms(user_input)
    print(f"主诉: {symptoms.chief_complaint}")
    print(f"症状: {symptoms.symptoms}")
    print(f"体征: {symptoms.signs}")
    print(f"患者信息: {symptoms.patient_info}")

asyncio.run(main())

# 同步使用
from subagents.symptom_extractor import extract_symptoms_sync

symptoms = extract_symptoms_sync(user_input)
print(symptoms)
```

---

## 📊 集成到MedicalAgent

P1已预留集成点，P3完成后可自动集成：

```python
# 在 core/agent.py 中
from planner import TodoManager
from subagents.symptom_extractor import extract_symptoms

class MedicalAgent:
    def __init__(self, ...):
        self.todo_manager = TodoManager()  # 自动初始化
        
    async def run(self, user_input: str, patient_id: str) -> Tuple[str, List[WorkflowStep]]:
        # 第1步：症状提取
        structured_symptoms = await extract_symptoms(user_input)
        
        # 第2步：生成待办任务
        self._generate_todos_from_symptoms(structured_symptoms)
        
        # 第3步：执行待办任务（原有流程）
        ...
```

---

## 🧪 测试策略

### planner.py 测试

```python
def test_add_and_get_todo():
    """测试添加和获取任务"""
    planner = TodoManager()
    task = planner.add_todo("测试任务", priority=3)
    assert planner.get_todo(task.id) == task

def test_priority_sorting():
    """测试优先级排序"""
    planner = TodoManager()
    planner.add_todo("任务1", priority=1)
    planner.add_todo("任务2", priority=5)
    todos = planner.get_todo_list(sort_by_priority=True)
    assert todos[0].priority == 5

def test_mark_completed():
    """测试标记完成"""
    planner = TodoManager()
    task = planner.add_todo("任务")
    planner.mark_completed(task.id)
    assert planner.get_todo(task.id).status == "completed"
```

### task_storage.py 测试

```python
def test_sqlite_save_and_load():
    """测试SQLite保存和加载"""
    storage = SQLiteStorage(":memory:")
    task = TodoTask(id="1", content="test", ...)
    assert storage.save_task(task)
    loaded = storage.load_task("1")
    assert loaded.content == "test"

def test_file_storage_persistence():
    """测试文件存储的持久化"""
    storage = FileStorage("./test_tasks")
    # 保存任务
    # 创建新实例重新加载
    # 验证数据是否持久化
```

### symptom_extractor.py 测试

```python
def test_extract_chief_complaint():
    """测试主诉提取"""
    extractor = SymptomExtractor(use_llm=False)  # 模式模式
    result = extractor.extract("我头痛厉害")
    assert "头痛" in result.chief_complaint

def test_extract_patient_info():
    """测试患者信息提取"""
    extractor = SymptomExtractor(use_llm=False)
    result = extractor.extract("30岁女性，体重60kg，对青霉素过敏")
    assert result.patient_info.age == 30
    assert result.patient_info.weight == 60
```

---

## 📋 实现检查清单

### planner.py
- [ ] TodoTask 数据类实现
- [ ] TodoManager 基类实现
- [ ] add_todo 方法
- [ ] get_todo_list 方法及排序逻辑
- [ ] update_todo 方法
- [ ] mark_completed 方法
- [ ] 优先级管理逻辑
- [ ] 依赖关系处理
- [ ] 与TaskStorage集成

### task_storage.py
- [ ] TaskStorage 抽象基类
- [ ] SQLiteStorage 完整实现
- [ ] FileStorage 完整实现
- [ ] 数据库 schema 创建
- [ ] CRUD 操作
- [ ] 批量操作
- [ ] 错误处理
- [ ] 事务管理（SQLite）

### subagents/symptom_extractor.py
- [ ] PatientInfo 数据类
- [ ] StructuredSymptoms 数据类
- [ ] SymptomExtractor 核心类
- [ ] extract 方法（LLM调用）
- [ ] 各项提取方法
- [ ] 验证逻辑
- [ ] 异步/同步版本
- [ ] 错误处理
- [ ] 日志记录

### 集成与测试
- [ ] 验证与P1的兼容性
- [ ] 单元测试覆盖度 >80%
- [ ] 集成测试验证
- [ ] 异常处理测试
- [ ] 性能测试（大量任务）
- [ ] 文档编写

---

## 🚀 优先级建议

1. **第一优先级**（核心功能）
   - planner.py: TodoTask + TodoManager 基类
   - task_storage.py: TaskStorage + SQLiteStorage（选择一种）
   - symptom_extractor.py: 基础提取逻辑

2. **第二优先级**（完整性）
   - FileStorage 实现
   - 异步支持
   - 高级查询方法

3. **第三优先级**（优化和扩展）
   - 缓存优化
   - 性能测试
   - 扩展功能（如ML-based症状检测）

---

## 📚 相关文件位置

- 异常定义：[exceptions.py](exceptions.py#L1)
- 配置管理：[config.py](config.py#L1)
- LLM客户端：[llm/client.py](llm/client.py#L1)
- 工具系统：[tools/base.py](tools/base.py#L1)
- 数据模型：[llm/schemas.py](llm/schemas.py#L1)
- 测试框架：[tests/conftest.py](tests/conftest.py#L1)

---

## 💡 实现建议

1. **保持模块独立性**：三个模块应该相互独立，通过明确的接口交互
2. **使用类型注解**：所有函数都应该有类型注解，便于IDE提示和测试
3. **完整的文档字符串**：遵循docstring规范，便于代码阅读
4. **异常处理**：自定义异常（如ExtractionError、StorageError等）
5. **日志记录**：使用logging记录关键步骤，便于调试
6. **单元测试**：每个公共方法都应有测试覆盖

祝你实现顺利！🎉
