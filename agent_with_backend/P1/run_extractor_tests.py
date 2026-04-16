#!/usr/bin/env python3
"""运行SymptomExtractor测试的脚本"""

import sys
import os
import unittest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.subagents.test_extractor import TestSymptomExtractor

def run_tests():
    """运行所有测试"""
    print("运行SymptomExtractor测试...")

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试方法
    test_cases = [
        'test_symptom_extractor_init',
        'test_extract_chief_complaint',
        'test_extract_patient_info',
        'test_extract_symptoms',
        'test_extract_with_rules',
        'test_validate_symptoms',
        'test_extract_method',
        'test_extract_async_method',
        'test_static_methods',
        'test_extract_signs',
        'test_extract_medical_history'
    ]

    for test_name in test_cases:
        suite.addTest(TestSymptomExtractor(test_name))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出结果
    print(f"\n{'='*60}")
    print(f"测试结果: {result.testsRun}个测试运行")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    # 返回退出码
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())