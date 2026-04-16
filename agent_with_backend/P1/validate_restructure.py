#!/usr/bin/env python3
"""验证subagents模块重构结果"""

import os
import sys
import re
from pathlib import Path

def check_directory_structure():
    """检查目录结构是否符合设计"""
    print("检查目录结构...")
    base_dir = Path(__file__).parent / "subagents"
    required_files = [
        "__init__.py",
        "models.py",
        "exceptions.py",
        "extractor.py",
        "api.py",
        "symptom_extractor.py"
    ]

    missing = []
    for f in required_files:
        if not (base_dir / f).exists():
            missing.append(f)

    if missing:
        print(f"  ✗ 缺失文件: {missing}")
        return False
    else:
        print("  ✓ 所有必需文件存在")
        return True

def check_init_file():
    """检查__init__.py是否符合重新导出模式（小于50行）"""
    print("检查__init__.py...")
    init_path = Path(__file__).parent / "subagents" / "__init__.py"
    with open(init_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    line_count = len(lines)
    print(f"  __init__.py行数: {line_count}")

    if line_count > 50:
        print(f"  ✗ 行数超过50行，当前{line_count}行")
        return False

    # 检查是否包含类定义（不应该有）
    class_defs = [i for i, line in enumerate(lines) if line.strip().startswith('class ')]
    if class_defs:
        print(f"  ✗ 发现类定义在第{class_defs}行")
        return False

    # 检查是否包含函数定义（不应该有，除了可能的logger）
    func_defs = [i for i, line in enumerate(lines) if line.strip().startswith('def ')]
    async_defs = [i for i, line in enumerate(lines) if line.strip().startswith('async def ')]
    if func_defs or async_defs:
        print(f"  ✗ 发现函数定义在第{func_defs + async_defs}行")
        return False

    print("  ✓ __init__.py符合重新导出模式")
    return True

def check_imports():
    """检查所有导入路径"""
    print("检查导入路径...")

    test_cases = [
        ("从subagents导入SymptomExtractor", "from subagents import SymptomExtractor"),
        ("从subagents.models导入PatientInfo", "from subagents.models import PatientInfo"),
        ("从subagents.exceptions导入ExtractionError", "from subagents.exceptions import ExtractionError"),
        ("从subagents.extractor导入SymptomExtractor", "from subagents.extractor import SymptomExtractor"),
        ("从subagents.api导入extract_symptoms", "from subagents.api import extract_symptoms"),
        ("从subagents.symptom_extractor导入extract_symptoms", "from subagents.symptom_extractor import extract_symptoms"),
    ]

    sys.path.insert(0, str(Path(__file__).parent))

    all_pass = True
    for desc, import_stmt in test_cases:
        try:
            exec(import_stmt)
            print(f"  ✓ {desc}")
        except Exception as e:
            print(f"  ✗ {desc}: {e}")
            all_pass = False

    return all_pass

def check_functionality():
    """检查基本功能"""
    print("检查基本功能...")

    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from subagents import extract_symptoms
        result = extract_symptoms("患者30岁，体重60kg，头痛，对青霉素过敏")

        # 验证提取结果
        assert result.patient_info.age == 30
        assert result.patient_info.weight == 60.0
        assert "头痛" in result.symptoms
        assert result.patient_info.allergies == ["青霉素"]

        print("  ✓ 症状提取功能正常")
        return True
    except Exception as e:
        print(f"  ✗ 功能测试失败: {e}")
        return False

def check_backward_compatibility():
    """检查向后兼容性（agent.py导入路径）"""
    print("检查向后兼容性...")

    sys.path.insert(0, str(Path(__file__).parent))

    # 模拟agent.py的导入路径
    try:
        # 注意：这里测试的是从subagents.symptom_extractor导入
        from subagents.symptom_extractor import extract_symptoms
        # 确保它是可调用的
        if callable(extract_symptoms):
            print("  ✓ agent.py的导入路径兼容")
            return True
        else:
            print("  ✗ extract_symptoms不可调用")
            return False
    except Exception as e:
        print(f"  ✗ 向后兼容性失败: {e}")
        return False

def main():
    print("=" * 60)
    print("subagents模块重构验证")
    print("=" * 60)

    checks = [
        ("目录结构", check_directory_structure),
        ("__init__.py规范", check_init_file),
        ("导入路径", check_imports),
        ("基本功能", check_functionality),
        ("向后兼容性", check_backward_compatibility),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ 检查过程中出错: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)

    all_pass = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_pass = False

    print("\n" + "=" * 60)
    if all_pass:
        print("✅ 所有验证通过！重构成功。")
        return 0
    else:
        print("❌ 部分验证失败，请检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())