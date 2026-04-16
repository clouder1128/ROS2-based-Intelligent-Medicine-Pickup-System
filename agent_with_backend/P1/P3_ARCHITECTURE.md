# P3 模块系统架构与数据流

## 📊 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      MedicalAgent (P1)                          │
│  核心AI助手，协调整个医疗咨询流程                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐    ┌────────────┐   ┌──────────────┐
   │症状提取 │    │规划器      │   │工具系统      │
   │Extractor│───▶│Planner     │──▶│ToolExecutor  │
   └─────────┘    └────────────┘   └──────────────┘
        │              │                   │
        │              ▼                   │
        │         ┌──────────────┐         │
        │         │任务管理器    │         │
        │         │TodoManager   │         │
        │         └──────┬───────┘         │
        │                │                 │
        │                ▼                 │
        │         ┌──────────────┐         │
        │         │任务存储      │         │
        │         │TaskStorage   │         │
        │         └──────┬───────┘         │
        │                │                 │
        └────────────────┼─────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
   ┌──────────────┐             ┌──────────────┐
   │SQLiteStorage │             │FileStorage   │
   │  .db文件     │             │  JSON文件    │
   └──────────────┘             └──────────────┘
```

## 🔄 数据流过程

### 第1步：用户输入 → 症状提取

```
用户输入
  "我是30岁女性，头痛3天，体温38.5度，对青霉素过敏"
           │
           ▼
   SymptomExtractor.extract()
           │
           ├─ extract_chief_complaint()     → "头痛3天"
           ├─ extract_patient_info()        → PatientInfo(age=30, gender=F, allergies=[...])
           ├─ extract_symptoms()            → ["头痛", "发热"]
           ├─ extract_signs()               → {"体温": 38.5}
           └─ extract_medical_history()     → None
           │
           ▼
   StructuredSymptoms
   {
     "chief_complaint": "头痛3天",
     "symptoms": ["头痛", "发热"],
     "signs": {"体温": 38.5},
     "patient_info": {
       "age": 30,
       "weight": null,
       "gender": "F",
       "allergies": ["青霉素"]
     },
     "medical_history": null
   }
```

### 第2步：症状 → 任务规划

```
StructuredSymptoms
           │
           ▼
   TodoManager.generate_from_symptoms()
           │
           ├─ Task 1: "询问患者体重"
           │         priority=5, category="symptom"
           │
           ├─ Task 2: "查询治疗头痛的药物"
           │         priority=4, category="query"
           │         dependencies=[Task1.id]
           │
           ├─ Task 3: "检查推荐药物与青霉素并发症"
           │         priority=5, category="check"
           │
           └─ Task 4: "计算青霉素类替代药的剂量"
                      priority=4, category="dosage"
                      │
                      ▼
   TaskStorage (持久化存储)
```

### 第3步：任务执行 → 结果反馈

```
待办任务队列
           │
           ├─ [进行中] Task 1: "询问患者体重"
           │    ▼
           │  获取信息: weight=60kg
           │    ▼
           │  [完成]
           │
           ├─ [待处理] Task 2: "查询治疗头痛的药物"
           │    (等待 Task 1 完成)
           │
           ├─ [待处理] Task 3: "检查推荐药物与青霉素并发症"
           │
           └─ [待处理] Task 4: "计算剂量"

摘要统计
{
  "total": 4,
  "pending": 2,
  "in_progress": 1,
  "completed": 1,
  "blocked": 0
}
```

## 🏗️ 模块交互图

```
┌─────────────────────────────────────────────────────────┐
│                  应用层 (MedicalAgent)                   │
│  调用各模块提供的接口完成医疗咨询工作流                 │
└──────────┬──────────────────────────────────────────────┘
           │
    ┌──────┴──────┬─────────────┬─────────────┐
    │             │             │             │
    ▼             ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐
│Symptom  │  │TodoManager   │ToolExecutor  │LLMClient │
│Extractor│  │          │    │                │
└────┬────┘  └────┬─────┘    └────────────┘  └──────────┘
     │            │
     │            ▼
     │       ┌──────────────┐
     │       │TaskStorage   │
     │       │(Abstract)    │
     │       └────┬─────────┘
     │            │
     │      ┌─────┴──────┐
     │      ▼            ▼
     │  ┌─────────┐  ┌──────────┐
     │  │SQLite   │  │FileStorage
     │  │Storage  │  │
     │  └─────────┘  └──────────┘
     │
     └── (返回结果)
         StructuredSymptoms
```

## 📋 持久化存储对比

### SQLiteStorage (推荐生产环境)

```
数据库文件: tasks.db
数据库表: tasks

结构:
┌──────────────────────────────────────────────┐
│ id (PK) │ content  │ status  │ priority │ ... │
├─────────┼──────────┼─────────┼──────────┼─────┤
│ uuid1   │ 询问症状 │ pending │ 5        │ ... │
│ uuid2   │ 查询药物 │ pending │ 4        │ ... │
│ uuid3   │ 检查过敏 │ complete│ 5        │ ... │
└──────────────────────────────────────────────┘

优势:
✓ 结构化查询 (SQL WHERE/ORDER BY)
✓ 事务支持, 数据一致性
✓ 性能优异 (大数据集)
✓ 支持并发读取
✓ 索引加速查询

劣势:
✗ 需要连接管理
✗ 需要显式关闭
```

### FileStorage (推荐开发环境)

```
数据目录: ./tasks_data/

结构:
tasks_data/
├── uuid1.json    ┬─ {"id": "uuid1", "content": "询问症状", ...}
├── uuid2.json    ├─ {"id": "uuid2", "content": "查询药物", ...}
├── uuid3.json    └─ {"id": "uuid3", "content": "检查过敏", ...}
└── ...

优势:
✓ 简单易用
✓ 隐式持久化 (自动保存)
✓ 支持版本控制 (git)
✓ 人工可读性强
✓ 无连接管理

劣势:
✗ 查询性能低 (n个文件读取)
✗ 不支持复杂查询
✗ 不线程安全 (高并发)
✗ 磁盘I/O开销
```

## 🔄 类的关系设计

```
TaskStorage (√)                           (✗) PlainObject
(Abstract)                                 (for reference only)
    △                                      
    │                                      
    ├─ SQLiteStorage ────┐                TodoTask
    │                    │                  △
    └─ FileStorage ──────┼─────┬───────────┤
                         │     │           │
                         ▼     ▼           │
                    Persistence        Properties
                         ▲               (id, content,
                         │                status,
                         │                priority,
                         │                category,
                         │                created_at,
                         │                updated_at,
                         │                completed_at,
                         │                notes,
                         │                related_symptoms,
                         │                dependencies)
                         │
                    TodoManager
                    (Manager)
                    
Methods:
- add_todo()
- get_todo()
- update_todo()
- delete_todo()
- get_summary()
- 其他查询方法
```

## 🧬 症状提取管道

```
用户输入 (自然语言)
    │
    ▼
选择提取模式
    │
    ├──── use_llm=False ────┐
    │                       │
    │                   规则提取
    │                       │
    │    ┌──────────────────┼──────────────────┐
    │    │                  │                  │
    │    ▼                  ▼                  ▼
    │ 年龄提取          症状提取              体征提取
    │ (正则表达式)      (关键词匹配)      (温度/心率等)
    │    │                  │                  │
    │    └──────────────────┼──────────────────┘
    │                       │
    │                       ▼
    │                  StructuredSymptoms
    │
    └──── use_llm=True ─────┐
                            │
                        LLM提取
                        (Claude/GPT)
                            │
                    生成结构化JSON
                            │
                            ▼
                    StructuredSymptoms

精度对照:
规则提取:  ★★★★☆  (~70-80%)  速度: ★★★★★ (~1-5ms)
LLM提取:   ★★★★★  (~95%+)    速度: ★☆☆☆☆  (~1-3s)
```

## 💾 数据持久化流程

```
内存                          存储
┌─────────────┐
│ TodoTask    │  save_task()  SQLite/File
│(in memory)  │─────────────▶ ┌──────────┐
└─────────────┘               │持久化    │
      △                       │存储      │
      │                       └────┬─────┘
      │ load_task()                │
      ├───────────────────────────┘
      │
      │ update()
      ▼
┌─────────────┐  save_task()
│TodoManager  │─────────────▶ (更新/新增)
│(cache)      │
└─────────────┘

工作流:
1. 用户操作 → TodoManager (内存更新)
2. TodoManager → TaskStorage (持久化)
3. 程序重启 → TaskStorage → TodoManager (恢复)
```

## 🎯 工作流状态机

```
创建Task
    │
    ▼
[PENDING] ◀─── pending状态
    │          (已创建，未开始)
    │
    ▼
mark_in_progress()
    │
    ▼
[IN_PROGRESS] ◀ in_progress状态
    │           (正在执行)
    ├──────────────┬──────────────┐
    │              │              │
    ▼              ▼              ▼
完成    异常    依赖阻碍
    │              │              │
    ▼              ▼              ▼
    mark_completed() mark_blocked()
    │              │
    ▼              ▼
[COMPLETED]   [BLOCKED]
    │              │
    ▼              ▼
完成备注    解除阻碍
    │         mark_pending()
    │              │
    └──────────────┘
         │
         ▼
    可删除/清理

关键特性:
• 状态转换清晰
• 支持多种中间状态
• 完整的声明周期管理
• 自动时间戳记录
```

## 📈 性能特性

```
操作性能对比:

TodoManager (内存)
├─ add_todo():           O(1)   ~<1ms
├─ get_todo():           O(1)   ~<1ms
├─ update_todo():        O(1)   ~<1ms
├─ delete_todo():        O(1)   ~<1ms
├─ get_todo_list():      O(n)   ~1-10ms
└─ 排序:                 O(n log n) ~5-50ms

SQLiteStorage (数据库)
├─ save_task():          O(log n) ~1-5ms
├─ load_task():          O(log n) ~1-2ms
├─ load_all_tasks():     O(n)    ~10-50ms
├─ update_task():        O(log n) ~1-5ms
└─ delete_task():        O(log n) ~1-2ms

FileStorage (文件)
├─ save_task():          O(1)    ~2-10ms (磁盘I/O)
├─ load_task():          O(1)    ~2-5ms
├─ load_all_tasks():     O(n)    ~20-100ms
├─ update_task():        O(1)    ~2-10ms
└─ delete_task():        O(1)    ~2-5ms

症状提取性能:
├─ 规则提取:             O(n)    ~1-5ms
└─ LLM提取:              O(1)    ~1-3秒 (含网络延迟)

(n = 任务数量)
```

---

有这个架构图，开发者能够快速理解P3模块的整体设计和数据流向。
