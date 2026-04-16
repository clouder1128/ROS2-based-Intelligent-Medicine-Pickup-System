#!/usr/bin/env python3
"""验证P1模块重构后的结构"""

import sys
sys.path.insert(0, "agent_with_backend")

print("=== P1模块重构验证 ===")

try:
    # 1. 测试planner模块导入
    from P1.planner import TodoManager, TodoTask, SQLiteStorage, FileStorage
    print("✅ planner模块导入成功")
    
    # 2. 测试从planner.models导入
    from P1.planner.models import TodoManager as TodoManager2
    print("✅ planner.models导入成功")
    
    # 3. 测试从planner.storage导入
    from P1.planner.storage import SQLiteStorage as SQLiteStorage2
    print("✅ planner.storage导入成功")
    
    # 4. 测试subagents模块导入
    from P1.subagents.symptom_extractor import extract_symptoms
    print("✅ subagents模块导入成功")
    
    # 5. 测试MedicalAgent导入和功能
    from P1.core.agent import MedicalAgent
    agent = MedicalAgent()
    print(f"✅ MedicalAgent导入成功，TodoManager类型: {type(agent.todo_manager).__name__}")
    
    # 6. 测试功能
    planner = TodoManager()
    task = planner.add_todo("验证测试任务", priority=5)
    print(f"✅ TodoManager功能正常，任务ID: {task.id}")
    
    symptoms = extract_symptoms("30岁女性，头痛3天，体温38度")
    print(f"✅ 症状提取正常，症状: {symptoms.symptoms}")
    
    storage = SQLiteStorage(":memory:")
    storage_planner = TodoManager(storage=storage)
    storage_task = storage_planner.add_todo("存储测试任务", priority=3)
    print(f"✅ 存储功能正常，任务ID: {storage_task.id}")
    
    print("\n🎉 所有验证通过！")
    print("✅ planner和subagents作为两个独立包运行正常")
    
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
