#!/usr/bin/env python3
"""
直接测试DeepSeek API连接
使用当前环境变量中的配置
"""

import os
import sys
import time
import signal
import logging
from typing import Dict, Any

# Add project root to Python path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up from tests/integration/ to P1/
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def timeout_handler(signum, frame):
    raise TimeoutError("API请求超时（30秒）")

def test_direct_connection() -> Dict[str, Any]:
    """直接测试API连接"""
    try:
        print("=" * 60)
        print("DeepSeek API直接连接测试")
        print("=" * 60)

        # 显示配置
        print("\n配置检查:")
        from core.config import Config
        config = Config.to_dict()
        for key, value in config.items():
            if "KEY" not in key and "TOKEN" not in key:
                print(f"  {key}: {value}")

        # 检查API密钥
        api_key = Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_AUTH_TOKEN
        if not api_key:
            return {"success": False, "error": "未设置API密钥"}

        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"  API密钥: {masked_key}")

        # 初始化LLM客户端
        print("\n初始化LLM客户端...")
        from llm.client import LLMClient
        client = LLMClient()
        print(f"✓ 客户端初始化成功")
        print(f"  提供商: {client.provider}")
        print(f"  模型: {Config.LLM_MODEL}")
        print(f"  Base URL: {Config.ANTHROPIC_BASE_URL}")

        # 准备测试消息
        test_messages = [
            {"role": "user", "content": "请用中文回复：'DeepSeek连接测试成功。' 请只回复这句话，不要添加其他内容。"}
        ]

        print(f"\n发送测试请求...")
        print(f"消息: {test_messages[0]['content']}")

        # 设置超时
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)

        start_time = time.time()
        try:
            response = client.chat(
                messages=test_messages,
                temperature=0.1,
                max_tokens=50
            )
            elapsed = time.time() - start_time
            signal.alarm(0)  # 取消超时

            print(f"✓ 请求成功 ({elapsed:.2f}秒)")

            # 分析响应
            content = response.get("content", "").strip()
            print(f"\n响应内容: {content}")

            # 检查响应是否符合预期
            expected_phrase = "DeepSeek连接测试成功"
            if expected_phrase in content:
                print(f"✓ 响应包含预期短语: '{expected_phrase}'")
                content_check = True
            else:
                print(f"⚠ 响应未包含预期短语: '{expected_phrase}'")
                print(f"  实际响应: '{content}'")
                content_check = False

            # 显示使用量
            usage = response.get("usage", {})
            if usage:
                print(f"\n使用量统计:")
                for key, value in usage.items():
                    print(f"  {key}: {value}")

            # 显示总体统计
            stats = LLMClient.get_stats()
            print(f"\n总体请求统计:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

            return {
                "success": True,
                "content_check": content_check,
                "content": content,
                "elapsed_time": elapsed,
                "usage": usage,
                "stats": stats,
                "error": None
            }

        except TimeoutError as e:
            signal.alarm(0)
            logger.error(f"请求超时: {e}")
            return {"success": False, "error": "请求超时", "timeout": True}
        except Exception as e:
            signal.alarm(0)
            logger.error(f"请求失败: {e}")
            return {"success": False, "error": str(e)}

    except ImportError as e:
        logger.error(f"导入失败: {e}")
        return {"success": False, "error": f"导入失败: {e}"}
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def main():
    print("\nP1医疗用药助手 - DeepSeek API直接测试")
    print("=" * 60)

    # 检查必要环境变量
    required_vars = ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"]
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"✗ 缺少必要环境变量: {missing_vars}")
        print("\n请设置以下环境变量:")
        print("  export ANTHROPIC_BASE_URL='https://api.deepseek.com/anthropic'")
        print("  export ANTHROPIC_AUTH_TOKEN='sk-your-api-key'")
        print("  export ANTHROPIC_MODEL='deepseek-chat' (可选)")
        print("  export LLM_PROVIDER='claude' (默认)")
        return 1

    print("环境变量检查通过")

    result = test_direct_connection()

    print("\n" + "=" * 60)
    if result.get("success"):
        print("✓ DeepSeek API连接测试成功！")
        if result.get("content_check"):
            print("✓ 响应内容符合预期")
        else:
            print("⚠ 响应内容未完全符合预期，但API连接正常")
        print(f"  响应时间: {result.get('elapsed_time', 0):.2f}秒")
        return 0
    else:
        print("✗ DeepSeek API连接测试失败")
        print(f"  错误: {result.get('error')}")

        # 提供调试建议
        print("\n调试建议:")
        print("1. 检查API密钥是否正确有效")
        print("2. 检查网络连接（特别是到DeepSeek API）")
        print("3. 验证ANTHROPIC_BASE_URL: https://api.deepseek.com/anthropic")
        print("4. 检查DeepSeek API服务状态")
        print("5. 检查API密钥是否有足够的额度")
        print("6. 检查是否有防火墙或代理限制")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)