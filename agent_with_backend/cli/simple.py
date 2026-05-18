#!/usr/bin/env python3
"""
P1医疗用药助手 - 简单交互式界面
提供基本的命令行对话功能

用法：
    python simple.py [患者ID]

这是一个简化的交互界面，适合快速测试和对话。
"""

import os
import sys
import logging
from typing import Optional

# 设置日志
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def simple_interactive_mode(patient_id: Optional[str] = None):
    """简单交互模式"""
    print("\n" + "=" * 60)
    print("P1医疗用药助手 - 简单交互模式")
    print("=" * 60)
    print("输入您的症状或问题，Agent会进行处理")
    print("输入 '/reset' 重置对话")
    print("输入 '/exit' 或按 Ctrl+C 退出")
    print("=" * 60)

    try:
        from agent.engine import MedicalAgent

        # 创建Agent
        agent = MedicalAgent()
        current_patient_id = patient_id or "default_patient"

        print(f"\n患者ID: {current_patient_id}")
        print("MedicalAgent已初始化，开始对话...\n")

        while True:
            try:
                # 获取用户输入
                user_input = input("您: ").strip()

                if not user_input:
                    continue

                # 处理特殊命令
                if user_input.lower() == "/exit":
                    print("\n退出程序...")
                    break
                elif user_input.lower() == "/reset":
                    agent.reset()
                    print("对话已重置")
                    continue
                elif user_input.lower() == "/help":
                    print("\n可用命令:")
                    print("  /reset  - 重置对话")
                    print("  /exit   - 退出程序")
                    print("  /help   - 显示帮助")
                    print("\n直接输入您的症状或问题进行咨询")
                    continue
                elif user_input.startswith("/"):
                    print(f"未知命令: {user_input}")
                    print("输入 '/help' 查看可用命令")
                    continue

                # 处理医疗咨询
                print("\n[处理中...]", end="", flush=True)

                try:
                    response, steps = agent.run(
                        user_input, patient_id=current_patient_id
                    )

                    # 显示响应
                    print("\n助手:", response)

                    # 显示统计信息
                    tool_calls = len([s for s in steps if s.get("type") == "tool_call"])
                    if tool_calls > 0:
                        print(f"[本次使用了 {tool_calls} 个工具调用]")

                except Exception as e:
                    print(f"\n处理失败: {e}")

                print()  # 空行

            except KeyboardInterrupt:
                print("\n\n检测到Ctrl+C，退出程序...")
                break
            except EOFError:
                print("\n\n检测到EOF，退出程序...")
                break
            except Exception as e:
                print(f"\n发生错误: {e}")
                continue

    except ImportError as e:
        print(f"导入失败: {e}")
        print("请确保已安装所有依赖：pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="P1医疗用药助手 - 简单交互模式")
    parser.add_argument("patient_id", nargs="?", help="患者ID（可选）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出模式")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    try:
        simple_interactive_mode(args.patient_id)
        print("\n程序结束")
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)


if __name__ == "__main__":
    main()
