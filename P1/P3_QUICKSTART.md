# P3 模块快速开始指南

## 📦 快速导入和使用

### 1. 规划器 (planner.py)

```python
from planner import TodoManager, TodoTask, TaskCategory

# 创建规划器（内存存储）
planner = TodoManager()

# 添加任务
task1 = planner.add_todo(
    content="询问患者的过敏史",
    priority=5,
    category=TaskCategory.SYMPTOM.value
)

task2 = planner.add_todo(
    content="查询相关药物",
    priority=4,
    category=TaskCategory.QUERY.value,
    dependencies=[task1.id]
)

# 查看待办项
pending = planner.get_pending_tasks()
print(f"待办项数: {len(pending)}")

# 标记完成
planner.mark_completed(task1.id, notes="患者无常见过敏")

# 获取摘要
summary = planner.get_summary()
print(f"总任务数: {summary['total']}")
print(f"待处理: {summary['pending']}")
print(f"已完成: {summary['completed']}")
```

### 2. 任务存储 (task_storage.py)

#### SQLite存储

```python
from task_storage import SQLiteStorage
from planner import TodoManager

# 创建SQLite存储
storage = SQLiteStorage("./medical_tasks.db")

# 创建带存储的规划器
planner = TodoManager(storage=storage)

# 添加任务（自动持久化）
task = planner.add_todo("询问症状", priority=5)

# 重启程序后，数据仍然存在
# 新建规划器，任务会自动加载
planner2 = TodoManager(storage=SQLiteStorage("./medical_tasks.db"))
print(planner2.get_summary())  # 任务数据已恢复
```

#### 文件存储

```python
from task_storage import FileStorage
from planner import TodoManager

# 创建文件存储
storage = FileStorage("./tasks_data")

# 创建带存储的规划器
planner = TodoManager(storage=storage)

# 任务以JSON文件形式保存在 ./tasks_data/ 目录中
# 每个任务一个文件：{task_id}.json
```

### 3. 症状提取 (subagents/symptom_extractor.py)

#### 规则提取（快速，无需LLM）

```python
from subagents.symptom_extractor import extract_symptoms

# 规则提取（默认）
user_input = "我是30岁女性，体重60kg，最近头痛厉害，还有点发烧，对阿司匹林过敏"
symptoms = extract_symptoms(user_input)

print(f"主诉: {symptoms.chief_complaint}")
print(f"症状: {symptoms.symptoms}")
print(f"患者年龄: {symptoms.patient_info.age}")
print(f"患者体重: {symptoms.patient_info.weight}")
print(f"过敏史: {symptoms.patient_info.allergies}")
print(f"体征: {symptoms.signs}")
```

#### LLM提取（精度高，需要LLM客户端）

```python
from llm import LLMClient
from subagents.symptom_extractor import extract_symptoms

# 初始化LLM客户端
llm_client = LLMClient()

# 使用LLM提取
symptoms = extract_symptoms(user_input, llm_client=llm_client)
print(symptoms.to_dict())
```

#### 异步提取

```python
import asyncio
from subagents.symptom_extractor import extract_symptoms_async

async def main():
    symptoms = await extract_symptoms_async(user_input)
    print(symptoms)

asyncio.run(main())
```

---

## 🔧 完整集成示例

```python
from planner import TodoManager
from task_storage import SQLiteStorage
from subagents.symptom_extractor import extract_symptoms

# 初始化存储和规划器
storage = SQLiteStorage("./medical_workflow.db")
planner = TodoManager(storage=storage)

# 处理患者输入
user_input = "我头很疼，还有点发烧，38度多"

# 第1步：提取症状
symptoms = extract_symptoms(user_input)
print(f"✓ 症状提取完成")
print(f"  主诉: {symptoms.chief_complaint}")
print(f"  症状: {', '.join(symptoms.symptoms)}")
print(f"  体征: {symptoms.signs}")

# 第2步：生成待办任务
task1 = planner.add_todo(
    content=f"患者主诉: {symptoms.chief_complaint}",
    priority=5,
    category="symptom"
)

if not symptoms.patient_info.allergies:
    task2 = planner.add_todo(
        content="询问患者过敏史",
        priority=5,
        category="check",
        dependencies=[task1.id]
    )

task3 = planner.add_todo(
    content="查询相关药物",
    priority=4,
    category="query"
)

# 第3步：查看待办项
pending = planner.get_pending_tasks()
print(f"\n✓ 生成待办项: {len(pending)} 个")
for task in pending:
    print(f"  [{task.priority}] {task.content}")

# 第4步：执行任务
planner.mark_in_progress(task1.id)
# 执行Agent逻辑...
planner.mark_completed(task1.id, notes="已收集患者基本信息")

# 第5步：查看进度
summary = planner.get_summary()
print(f"\n✓ 任务进度统计:")
print(f"  总数: {summary['total']}")
print(f"  待处理: {summary['pending']}")
print(f"  进行中: {summary['in_progress']}")
print(f"  已完成: {summary['completed']}")
```

---

## 🧪 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-asyncio

# 运行所有测试
pytest -v

# 运行特定模块的测试
pytest tests/test_planner.py -v
pytest tests/test_task_storage.py -v
pytest tests/test_symptom_extractor.py -v

# 运行并收集覆盖率
pytest --cov=planner --cov=task_storage --cov=subagents --cov-report=html
```

---

## 📊 数据持久化说明

### SQLite存储

**优势**：
- 结构化查询，性能最优
- 支持事务和并发
- 单文件存储，易于备份

**劣势**：
- 需要处理数据库连接
- 需要关闭连接以避免资源泄漏

**最佳实践**：
```python
storage = SQLiteStorage("./tasks.db")
try:
    # 使用存储
    planner = TodoManager(storage=storage)
    ...
finally:
    storage.close()  # 一定要关闭连接
```

### 文件存储

**优势**：
- 简单易用，无需数据库
- 支持版本控制（JSON文件）
- 人工可读

**劣势**：
- 查询性能较低
- 高并发时容易出现冲突

**最佳实践**：
```python
from task_storage import FileStorage

storage = FileStorage("./tasks_data")
planner = TodoManager(storage=storage)

# 文件自动保存到 ./tasks_data/{task_id}.json
# 可以使用版本控制追踪变化
```

---

## ⚙️ 集成到MedicalAgent

当P1更新以支持P3模块后，集成会自动完成：

```python
from core.agent import MedicalAgent
from planner import TodoManager
from task_storage import SQLiteStorage

# MedicalAgent会自动使用P3模块
agent = MedicalAgent()

# 运行对话，自动调用症状提取和任务规划
response, steps = agent.run(
    "我头痛，有点发烧",
    patient_id="patient_123"
)

# 查看任务列表
if hasattr(agent, 'todo_manager'):
    print(agent.todo_manager.get_summary())
```

---

## 🎯 开发路线图

### Phase 1: 核心功能（已完成）
- [x] TodoTask 数据类
- [x] TodoManager 基类
- [x] SQLiteStorage 实现
- [x] FileStorage 实现
- [x] SymptomExtractor 实现

### Phase 2: 增强功能（建议）
- [ ] 高级查询方法（按日期、按优先级聚合等）
- [ ] 任务分配和权限管理
- [ ] 任务历史和审计日志
- [ ] 缓存优化（Redis集成）
- [ ] 批量API操作

### Phase 3: 集成与优化
- [ ] 与MedicalAgent的完整集成
- [ ] 单元测试覆盖（>90%）
- [ ] 性能优化（大量任务处理）
- [ ] 文档和示例完善

---

## 🔗 相关文档

- [完整P3实现指南](P3_IMPLEMENTATION_GUIDE.md)
- [P1 README](README.md)
- [项目文档](../AI%20开药助手%20—— 团队项目说明文档%20ver%203.0.md)

---

祝开发顺利！💪
