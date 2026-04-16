#!/usr/bin/env python3
"""Test script for config extensions"""

import sys
import os
sys.path.insert(0, '.')

def test_config_interactive_workflow():
    """测试交互式工作流配置"""
    from core.config import Config

    # 验证配置项存在
    assert hasattr(Config, 'ENABLE_LLM_SYMPTOM_EXTRACTION')
    assert hasattr(Config, 'NEGATION_WORDS')

    # 验证默认值
    assert Config.ENABLE_LLM_SYMPTOM_EXTRACTION == True  # 默认true

    # 验证否定词列表
    assert isinstance(Config.NEGATION_WORDS, list)
    assert "无" in Config.NEGATION_WORDS
    assert "没有" in Config.NEGATION_WORDS
    assert "不" in Config.NEGATION_WORDS
    print("✓ Config interactive workflow test passed")

def test_config_env_override():
    """测试环境变量覆盖配置"""
    import os
    from core.config import Config

    # 保存原始环境变量
    original_env = os.getenv("ENABLE_LLM_SYMPTOM_EXTRACTION")

    try:
        # 测试false值
        os.environ["ENABLE_LLM_SYMPTOM_EXTRACTION"] = "false"
        from importlib import reload
        import core.config
        reload(core.config)
        from core.config import Config as ReloadedConfig

        assert ReloadedConfig.ENABLE_LLM_SYMPTOM_EXTRACTION == False

        # 测试true值
        os.environ["ENABLE_LLM_SYMPTOM_EXTRACTION"] = "true"
        reload(core.config)
        from core.config import Config as ReloadedConfig2

        assert ReloadedConfig2.ENABLE_LLM_SYMPTOM_EXTRACTION == True
        print("✓ Config environment override test passed")

    finally:
        # 恢复环境变量
        if original_env:
            os.environ["ENABLE_LLM_SYMPTOM_EXTRACTION"] = original_env
        else:
            os.environ.pop("ENABLE_LLM_SYMPTOM_EXTRACTION", None)
        # 重新加载配置
        from importlib import reload
        import core.config
        reload(core.config)

if __name__ == "__main__":
    try:
        test_config_interactive_workflow()
        test_config_env_override()
        print("\nAll config tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)