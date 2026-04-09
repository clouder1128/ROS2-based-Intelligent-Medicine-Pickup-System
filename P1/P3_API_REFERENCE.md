# P3 模块 API 快速参考

## 🎯 核心类 API

### TodoTask - 任务数据类

```python
from planner import TodoTask, TaskStatus, TaskCategory

# 创建任务
task = TodoTask(
    content: str                    # 任务内容
    priority: int = 3               # 优先级 1-5
    status: str = "pending"         # 任务状态
    category: str = "other"         # 任务分类
    related_symptoms: List[str]     # 关联症状
    dependencies: List[str]         # 依赖任务ID
)

# 任务状态方法
task.mark_completed(notes: str)     # 标记完成
task.mark_in_progress()             # 标记进行中
task.mark_blocked()                 # 标记被阻止
task.mark_pending()                 # 标记待处理

# 查询方法
task.is_completed() -> bool         # 是否完成
task.is_pending() -> bool           # 是否待处理
task.get_age() -> float             # 任务年龄（秒）
task.get_completion_time() -> float # 完成耗时（秒）

# 序列化方法
task.to_dict() -> Dict              # 转为字典
TodoTask.from_dict(data) -> TodoTask # 从字典创建
```

### TodoManager - 任务管理器

```python
from planner import TodoManager

# 初始化
manager = TodoManager(storage=None)

# 添加任务
task = manager.add_todo(
    content: str,
    priority: int = 3,
    category: str = "other",
    related_symptoms: List[str] = None,
    dependencies: List[str] = None
) -> TodoTask

# 查询任务
manager.get_todo(task_id: str) -> Optional[TodoTask]
manager.get_todo_list(
    filter_by_status: str = None,
    sort_by_priority: bool = True,
    sort_ascending: bool = False
) -> List[TodoTask]

# 便捷查询
manager.get_pending_tasks() -> List[TodoTask]
manager.get_high_priority_tasks(threshold: int = 4) -> List[TodoTask]
manager.get_tasks_by_category(category: str) -> List[TodoTask]
manager.get_tasks_by_symptom(symptom: str) -> List[TodoTask]

# 更新任务
manager.update_todo(
    task_id: str,
    content: str = None,
    priority: int = None,
    status: str = None,
    category: str = None,
    notes: str = None
) -> bool

# 标记任务
manager.mark_completed(task_id: str, notes: str = None) -> bool
manager.mark_in_progress(task_id: str) -> bool

# 删除任务
manager.delete_todo(task_id: str) -> bool
manager.clear_completed_tasks() -> int

# 统计
manager.get_summary() -> Dict[str, int]
# 返回: {
#   'total': 总数,
#   'pending': 待处理数,
#   'in_progress': 进行中数,
#   'completed': 完成数,
#   'blocked': 被阻止数
# }
```

---

## 💾 存储层 API

### TaskStorage - 存储基类

```python
from task_storage import TaskStorage, SQLiteStorage, FileStorage

# SQLite存储（推荐生产环境）
storage = SQLiteStorage(
    db_path: str = "./tasks.db"    # ":memory:" 表示内存数据库
)

# 文件存储（推荐开发环境）
storage = FileStorage(
    data_dir: str = "./tasks_data"  # 数据目录
)

# 通用接口
storage.save_task(task: TodoTask) -> bool
storage.load_task(task_id: str) -> Optional[TodoTask]
storage.load_all_tasks() -> List[TodoTask]
storage.update_task(task_id: str, updates: Dict) -> bool
storage.delete_task(task_id: str) -> bool
storage.delete_all_tasks(filter_by_status: str = None) -> int

# SQLite特有方法
storage.get_tasks_by_status(status: str) -> List[TodoTask]
storage.get_tasks_by_priority(min_priority: int) -> List[TodoTask]
storage.close()  # 关闭数据库连接

# FileStorage特有方法
# 无特有方法，使用通用接口
```

---

## 🏥 症状提取 API

### PatientInfo - 患者信息

```python
from subagents.symptom_extractor import PatientInfo

info = PatientInfo(
    age: Optional[int] = None         # 年龄
    weight: Optional[float] = None    # 体重（kg）
    gender: Optional[str] = None      # 性别 M/F/other
    allergies: Optional[List[str]] = None  # 过敏史
)

# 序列化
info.to_dict() -> Dict
PatientInfo.from_dict(data: Dict) -> PatientInfo
```

### StructuredSymptoms - 结构化症状

```python
from subagents.symptom_extractor import StructuredSymptoms

symptoms = StructuredSymptoms(
    chief_complaint: str              # 主诉
    symptoms: List[str] = []          # 症状列表
    signs: Dict[str, Any] = {}        # 体征
    patient_info: PatientInfo = PatientInfo()
    medical_history: Dict = None      # 既往史
)

# 序列化
symptoms.to_dict() -> Dict
StructuredSymptoms.from_dict(data: Dict) -> StructuredSymptoms
```

### SymptomExtractor - 症状提取器

```python
from subagents.symptom_extractor import SymptomExtractor, extract_symptoms

# 使用便捷函数（推荐）
symptoms = extract_symptoms(
    user_input: str,
    llm_client = None  # 不提供则用规则模式，提供则用LLM模式
) -> StructuredSymptoms

# 异步版本
symptoms = await extract_symptoms_async(user_input, llm_client)

# 或用类进行细粒度控制
extractor = SymptomExtractor(llm_client=None, use_llm=False)

# 完整提取
symptoms = extractor.extract(text: str) -> StructuredSymptoms
symptoms = await extractor.extract_async(text: str) -> StructuredSymptoms

# 单项提取
extractor.extract_chief_complaint(text: str) -> str
extractor.extract_patient_info(text: str) -> PatientInfo
extractor.extract_symptoms(text: str) -> List[str]
extractor.extract_signs(text: str) -> Dict[str, Any]
extractor.extract_medical_history(text: str) -> Optional[Dict]

# 验证
is_valid, error = extractor.validate_symptoms(symptoms)
```

---

## 📊 枚举值速查表

### TaskStatus (任务状态)

```python
from planner import TaskStatus

TaskStatus.PENDING.value        # "pending" - 待处理
TaskStatus.IN_PROGRESS.value    # "in_progress" - 进行中
TaskStatus.COMPLETED.value      # "completed" - 已完成
TaskStatus.BLOCKED.value        # "blocked" - 被阻止
```

### TaskCategory (任务分类)

```python
from planner import TaskCategory

TaskCategory.SYMPTOM.value      # "symptom" - 症状相关
TaskCategory.QUERY.value        # "query" - 查询相关
TaskCategory.CHECK.value        # "check" - 检查相关
TaskCategory.DOSAGE.value       # "dosage" - 剂量相关
TaskCategory.APPROVAL.value     # "approval" - 审批相关
TaskCategory.OTHER.value        # "other" - 其他
```

### Gender (性别)

```python
from subagents.symptom_extractor import Gender

Gender.MALE.value               # "M" - 男性
Gender.FEMALE.value             # "F" - 女性
Gender.OTHER.value              # "other" - 其他
```

---

## 🔧 常见用法模式

### 模式 1: 简单内存规划

```python
from planner import TodoManager

planner = TodoManager()
task = planner.add_todo("查询药物", priority=4)
planner.mark_completed(task.id)
print(planner.get_summary())
```

### 模式 2: SQLite持久化

```python
from planner import TodoManager
from task_storage import SQLiteStorage

storage = SQLiteStorage("./tasks.db")
planner = TodoManager(storage=storage)

# 添加、更新任务（自动保存）
# 程序重启后数据仍存在
```

### 模式 3: 症状提取（规则）

```python
from subagents.symptom_extractor import extract_symptoms

symptoms = extract_symptoms("30岁女性，头痛，体温38度")
print(f"年龄: {symptoms.patient_info.age}")
print(f"症状: {symptoms.symptoms}")
```

### 模式 4: 症状提取（LLM）

```python
from llm import LLMClient
from subagents.symptom_extractor import extract_symptoms

llm = LLMClient()
symptoms = extract_symptoms(user_input, llm_client=llm)
```

### 模式 5: 完整流程

```python
from planner import TodoManager
from task_storage import SQLiteStorage
from subagents.symptom_extractor import extract_symptoms

# 初始化
storage = SQLiteStorage("./workflow.db")
planner = TodoManager(storage=storage)

# 提取症状
symptoms = extract_symptoms("我头痛")

# 生成任务
planner.add_todo(
    f"患者主诉: {symptoms.chief_complaint}",
    priority=5,
    category="symptom"
)

# 查看进度
print(planner.get_summary())
```

---

## ⚠️ 常见错误

### 错误 1: 忘记关闭SQLite连接

```python
# ❌ 错误
storage = SQLiteStorage("./tasks.db")
planner = TodoManager(storage=storage)
# 不关闭，资源泄漏

# ✅ 正确
storage = SQLiteStorage("./tasks.db")
try:
    planner = TodoManager(storage=storage)
    # 使用planner
finally:
    storage.close()
```

### 错误 2: 使用无效优先级

```python
# ❌ 错误
task = TodoTask(content="任务", priority=10)  # ValueError!

# ✅ 正确
task = TodoTask(content="任务", priority=5)   # 1-5有效
```

### 错误 3: 空输入

```python
# ❌ 错误
from subagents.symptom_extractor import extract_symptoms
symptoms = extract_symptoms("")  # ExtractionError!

# ✅ 正确
symptoms = extract_symptoms("我感觉不舒服")
```

---

## 📚 文档导航

| 文档 | 用途 |
|------|------|
| [P3_IMPLEMENTATION_GUIDE.md](P3_IMPLEMENTATION_GUIDE.md) | 完整的实现细节和设计文档 |
| [P3_QUICKSTART.md](P3_QUICKSTART.md) | 快速开始和集成示例 |
| [P3_SUMMARY.md](P3_SUMMARY.md) | 实现总结和检查清单 |
| 本文件 | API 快速参考 |

---

## 🆘 获取帮助

1. **查看docstring** - 所有类和方法都有详细文档
2. **阅读guide** - P3_IMPLEMENTATION_GUIDE.md有完整说明
3. **运行示例** - P3_QUICKSTART.md有可运行的代码
4. **查看测试** - tests/test_p3_*.py有使用示例

---

**版本**: 1.0  
**最后更新**: 2026年4月  
**维护者**: P3团队
