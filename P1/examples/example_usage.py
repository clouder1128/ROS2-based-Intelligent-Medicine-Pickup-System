#!/usr/bin/env python3
"""
P1医疗用药助手Agent使用示例
演示如何配置和使用MedicalAgent进行医疗咨询

注意：运行前请先配置环境变量（参考README.md）
"""

import os
import sys
import logging
from typing import Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_basic_usage() -> None:
    """演示基本使用"""
    print("=" * 60)
    print("P1医疗用药助手 - 基本使用演示")
    print("=" * 60)

    try:
        from core.config import Config
        from core.agent import MedicalAgent

        # 显示配置
        print("\n1. 检查配置...")
        config_summary = Config.to_dict()
        print(f"   提供商: {config_summary.get('LLM_PROVIDER')}")
        print(f"   模型: {config_summary.get('LLM_MODEL')}")
        print(f"   温度: {config_summary.get('LLM_TEMPERATURE')}")
        print(f"   最大迭代: {config_summary.get('MAX_ITERATIONS')}")

        # 创建Agent
        print("\n2. 创建MedicalAgent...")
        agent = MedicalAgent()
        print("   ✓ Agent创建成功")

        # 模拟简单咨询
        print("\n3. 模拟医疗咨询...")
        test_cases = [
            "患者头痛，需要用药建议",
            "我感冒了，流鼻涕、打喷嚏",
            "孩子发烧38度，应该怎么办"
        ]

        for i, query in enumerate(test_cases[:1]):  # 只运行第一个测试，避免过多API调用
            print(f"\n   咨询 {i+1}: {query}")
            try:
                response, steps = agent.run(query, patient_id=f"demo_patient_{i}")
                print(f"   响应: {response[:100]}..." if len(response) > 100 else f"   响应: {response}")
                print(f"   执行步骤: {len(steps)}步")

                # 显示工具调用详情
                tool_steps = [s for s in steps if s.get('type') == 'tool_call']
                if tool_steps:
                    print(f"   工具调用: {len(tool_steps)}次")
                    for ts in tool_steps:
                        print(f"     - {ts.get('tool')}: {str(ts.get('input', {}))[:50]}...")

                # 查看工作流状态
                workflow = agent.get_workflow_state(f"demo_patient_{i}")
                if workflow:
                    print(f"   工作流状态: {workflow.get('current_step', '未知')}")

                # 重置agent进行下一个测试
                agent.reset()

            except Exception as e:
                print(f"   咨询失败: {e}")
                logger.exception("咨询详细错误")

        print("\n4. 演示完成")
        print("=" * 60)

    except ImportError as e:
        print(f"导入失败: {e}")
        print("请确保已安装所有依赖：pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"演示失败: {e}")
        logger.exception("详细错误信息")
        sys.exit(1)

def demo_config_check() -> None:
    """演示配置检查"""
    print("\n" + "=" * 60)
    print("配置检查演示")
    print("=" * 60)

    try:
        from core.config import Config

        print("\n当前环境变量:")
        env_vars = [
            "LLM_PROVIDER",
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_MODEL",
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY"
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

        print("\n配置验证:")
        try:
            Config.validate()
            print("  ✓ 配置验证通过")

            config_dict = Config.to_dict()
            print("\n配置摘要:")
            for key, value in config_dict.items():
                if "KEY" not in key and "TOKEN" not in key:
                    print(f"  {key}: {value}")

        except Exception as e:
            print(f"  ✗ 配置验证失败: {e}")

    except ImportError as e:
        print(f"导入失败: {e}")

def demo_llm_client() -> None:
    """演示LLM客户端使用"""
    print("\n" + "=" * 60)
    print("LLM客户端演示")
    print("=" * 60)

    try:
        from llm.client import LLMClient

        print("\n1. 创建LLM客户端...")
        client = LLMClient()
        print(f"   ✓ 客户端创建成功，提供商: {client.provider}")

        print("\n2. 发送测试消息...")
        test_messages = [
            {"role": "user", "content": "请用中文回复'测试成功'"}
        ]

        # 注意：这会产生实际的API调用
        run_api_test = input("\n是否进行实际API测试？(y/n): ").strip().lower()
        if run_api_test == 'y':
            try:
                response = client.chat(
                    messages=test_messages,
                    temperature=0.1,
                    max_tokens=50
                )

                content = response.get("content", "")
                print(f"   响应: {content}")
                print(f"   工具调用: {len(response.get('tool_calls', []))}个")

                stats = LLMClient.get_stats()
                print(f"\n3. 统计信息:")
                print(f"   请求次数: {stats.get('requests', 0)}")
                print(f"   估算tokens: {stats.get('estimated_tokens', 0)}")

            except Exception as e:
                print(f"   API测试失败: {e}")
                print("   请检查API配置和网络连接")
        else:
            print("   跳过实际API测试")

    except ImportError as e:
        print(f"导入失败: {e}")

def main() -> None:
    """主函数"""
    print("\nP1医疗用药助手Agent - 使用示例")
    print("=" * 60)

    # 显示选项
    print("\n选择演示内容:")
    print("1. 配置检查")
    print("2. LLM客户端演示")
    print("3. 完整MedicalAgent演示")
    print("4. 全部演示")

    choice = input("\n请输入选项 (1-4): ").strip()

    if choice == "1":
        demo_config_check()
    elif choice == "2":
        demo_llm_client()
    elif choice == "3":
        demo_basic_usage()
    elif choice == "4":
        demo_config_check()
        demo_llm_client()
        demo_basic_usage()
    else:
        print("无效选项，运行完整演示")
        demo_config_check()
        demo_llm_client()
        demo_basic_usage()

    print("\n" + "=" * 60)
    print("示例演示完成")
    print("更多信息请参考 README.md")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n演示发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)