#!/usr/bin/env python3
"""
DeepSeek API集成测试脚本
测试P1系统与DeepSeek API的实际连接

注意：需要有效的DeepSeek API密钥
设置环境变量：
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="sk-your-api-key"
export ANTHROPIC_MODEL="deepseek-chat"
export LLM_PROVIDER="claude"
"""

import os
import sys
import logging
from typing import Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_deepseek_configuration() -> Dict[str, Any]:
    """测试DeepSeek配置"""
    try:
        from config import Config

        print("=" * 60)
        print("DeepSeek配置测试")
        print("=" * 60)

        # 显示当前配置
        config_dict = Config.to_dict()
        print("\n当前配置:")
        for key, value in config_dict.items():
            print(f"  {key}: {value}")

        # 检查关键配置
        print("\n关键配置检查:")
        checks = []

        if Config.LLM_PROVIDER == "claude":
            checks.append(("✓ LLM提供商", f"claude (兼容DeepSeek)"))
        else:
            checks.append(("✗ LLM提供商", f"应为'claude'，当前为'{Config.LLM_PROVIDER}'"))

        if Config.ANTHROPIC_BASE_URL:
            checks.append(("✓ DeepSeek API端点", Config.ANTHROPIC_BASE_URL))
        else:
            checks.append(("✗ DeepSeek API端点", "未设置"))

        if Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_AUTH_TOKEN:
            key = Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_AUTH_TOKEN
            masked_key = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
            checks.append(("✓ API密钥", f"已设置 ({masked_key})"))
        else:
            checks.append(("✗ API密钥", "未设置"))

        if Config.LLM_MODEL:
            checks.append(("✓ 模型", Config.LLM_MODEL))
        else:
            checks.append(("✗ 模型", "未设置"))

        for check, value in checks:
            print(f"  {check}: {value}")

        return {
            "config": config_dict,
            "checks": checks,
            "all_passed": all(check.startswith("✓") for check, _ in checks)
        }

    except Exception as e:
        logger.error(f"配置测试失败: {e}")
        return {"error": str(e), "all_passed": False}

def test_deepseek_api_connection() -> Dict[str, Any]:
    """测试DeepSeek API连接"""
    try:
        from llm.client import LLMClient

        print("\n" + "=" * 60)
        print("DeepSeek API连接测试")
        print("=" * 60)

        # 初始化LLM客户端
        print("\n初始化LLM客户端...")
        client = LLMClient()
        print(f"✓ 客户端初始化成功，提供商: {client.provider}")

        # 简单的测试消息
        test_messages = [
            {"role": "user", "content": "Hello, please respond with a short greeting."}
        ]

        print("\n发送测试消息...")
        print(f"消息: {test_messages[0]['content']}")

        try:
            # 发送请求（设置较短的超时时间）
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("API请求超时")

            # 设置超时处理
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30秒超时

            response = client.chat(
                messages=test_messages,
                temperature=0.1,
                max_tokens=100
            )

            signal.alarm(0)  # 取消超时

            print("\n✓ API响应接收成功")

            # 分析响应
            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            usage = response.get("usage", {})

            print(f"\n响应内容: {content[:100]}..." if len(content) > 100 else f"响应内容: {content}")
            print(f"工具调用: {len(tool_calls)} 个")

            if usage:
                print(f"使用量: {usage}")

            # 获取统计信息
            stats = LLMClient.get_stats()
            print(f"\n请求统计: {stats}")

            return {
                "success": True,
                "content": content,
                "tool_calls": tool_calls,
                "usage": usage,
                "stats": stats,
                "error": None
            }

        except TimeoutError as e:
            logger.error(f"API请求超时: {e}")
            return {"success": False, "error": "请求超时", "timeout": True}
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            return {"success": False, "error": str(e)}

    except Exception as e:
        logger.error(f"API连接测试失败: {e}")
        return {"success": False, "error": str(e)}

def test_medical_agent_integration() -> Dict[str, Any]:
    """测试MedicalAgent与DeepSeek的集成"""
    try:
        print("\n" + "=" * 60)
        print("MedicalAgent集成测试")
        print("=" * 60)

        # 注意：这里不实际运行完整的MedicalAgent，因为需要药房API
        # 只测试初始化
        from core.agent import MedicalAgent

        print("\n初始化MedicalAgent...")
        agent = MedicalAgent()
        print("✓ MedicalAgent初始化成功")

        # 检查agent的LLM客户端配置
        if hasattr(agent, 'llm_client'):
            print(f"✓ Agent包含LLM客户端，提供商: {agent.llm_client.provider}")

        return {
            "success": True,
            "agent_initialized": True,
            "error": None
        }

    except Exception as e:
        logger.error(f"MedicalAgent集成测试失败: {e}")
        return {"success": False, "error": str(e)}

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("P1医疗用药助手 - DeepSeek API集成测试")
    print("=" * 60)

    # 检查环境变量
    print("\n环境变量检查:")
    env_vars = [
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL",
        "LLM_PROVIDER"
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var or "TOKEN" in var:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"  {var}: {masked}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: 未设置")

    # 运行测试
    config_result = test_deepseek_configuration()

    if not config_result.get("all_passed", False):
        print("\n✗ 配置检查未通过，跳过API测试")
        if "error" in config_result:
            print(f"错误: {config_result['error']}")
        return 1

    # 询问是否进行API测试
    print("\n" + "-" * 60)
    api_test = input("是否进行实际的API连接测试？(y/n): ").strip().lower()

    if api_test == 'y':
        api_result = test_deepseek_api_connection()

        if api_result.get("success", False):
            print("\n✓ DeepSeek API连接测试通过")

            # 询问是否进行Agent集成测试
            agent_test = input("\n是否进行MedicalAgent集成测试？(y/n): ").strip().lower()
            if agent_test == 'y':
                agent_result = test_medical_agent_integration()
                if agent_result.get("success", False):
                    print("\n✓ 所有测试通过！DeepSeek配置成功。")
                    return 0
                else:
                    print(f"\n✗ MedicalAgent集成测试失败: {agent_result.get('error')}")
                    return 1
            else:
                print("\n✓ DeepSeek API连接测试完成，跳过Agent集成测试")
                return 0
        else:
            print(f"\n✗ DeepSeek API连接测试失败: {api_result.get('error')}")

            # 提供调试建议
            print("\n调试建议:")
            print("1. 检查API密钥是否正确")
            print("2. 检查网络连接")
            print("3. 检查DeepSeek API服务状态")
            print("4. 检查速率限制")
            print("5. 验证ANTHROPIC_BASE_URL是否为: https://api.deepseek.com/anthropic")

            return 1
    else:
        print("\n跳过API连接测试，仅验证配置")
        print("✓ 配置验证完成")
        return 0

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