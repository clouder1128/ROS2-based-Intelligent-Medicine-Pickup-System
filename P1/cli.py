#!/usr/bin/env python3
"""
P1医疗用药助手 - 交互式命令行界面
提供多轮对话功能，支持特殊命令和会话管理

用法：
    python cli.py [患者ID] [--save-dir SAVE_DIR]

示例：
    python cli.py patient_123
    python cli.py --save-dir ./sessions
"""

import os
import sys
import argparse
import logging
import readline  # 用于命令行历史记录
from typing import Optional, List, Dict, Any
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class InteractiveCLI:
    """交互式命令行界面"""

    def __init__(self, patient_id: Optional[str] = None, save_dir: str = "./sessions"):
        """
        初始化交互式CLI

        Args:
            patient_id: 患者ID，如果为None则自动生成
            save_dir: 会话保存目录
        """
        self.patient_id = patient_id or self._generate_patient_id()
        self.save_dir = save_dir
        self.agent = None
        self.session_file = None
        self.command_history: List[str] = []

        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)

        # 特殊命令映射
        self.commands = {
            "/help": self._cmd_help,
            "/reset": self._cmd_reset,
            "/save": self._cmd_save,
            "/load": self._cmd_load,
            "/status": self._cmd_status,
            "/history": self._cmd_history,
            "/workflow": self._cmd_workflow,
            "/stats": self._cmd_stats,
            "/exit": self._cmd_exit,
            "/quit": self._cmd_exit,
            "/clear": self._cmd_clear,
            "/patient": self._cmd_patient,
        }

    def _generate_patient_id(self) -> str:
        """生成患者ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"patient_{timestamp}"

    def _print_banner(self) -> None:
        """打印欢迎横幅"""
        print("\n" + "=" * 60)
        print("P1医疗用药助手 - 交互式命令行界面")
        print("=" * 60)
        print(f"患者ID: {self.patient_id}")
        print(f"会话目录: {self.save_dir}")
        print("输入 '/help' 查看可用命令")
        print("输入 '/exit' 退出程序")
        print("=" * 60 + "\n")

    def _cmd_help(self, args: List[str] = None) -> bool:
        """显示帮助信息"""
        print("\n" + "=" * 60)
        print("可用命令:")
        print("=" * 60)
        print("  /help                - 显示此帮助信息")
        print("  /reset               - 重置当前会话（开始新对话）")
        print("  /save [文件名]       - 保存当前会话状态")
        print("  /load <文件名>       - 加载会话状态")
        print("  /status              - 显示当前会话状态")
        print("  /history             - 显示对话历史")
        print("  /workflow            - 显示工作流状态")
        print("  /stats               - 显示统计信息")
        print("  /patient [新ID]      - 查看或更改患者ID")
        print("  /clear               - 清空屏幕")
        print("  /exit, /quit         - 退出程序")
        print("\n常规使用:")
        print("  直接输入您的症状或问题，Agent会进行处理")
        print("  例如: '患者头痛，需要用药建议'")
        print("  例如: '我对青霉素过敏，可以吃什么药？'")
        print("=" * 60)
        return False  # 不退出

    def _cmd_reset(self, args: List[str] = None) -> bool:
        """重置会话"""
        if self.agent:
            self.agent.reset()
            print("✓ 会话已重置")
            self.session_file = None
        else:
            print("! Agent未初始化")
        return False

    def _cmd_save(self, args: List[str] = None) -> bool:
        """保存会话状态"""
        if not self.agent:
            print("! Agent未初始化，无法保存")
            return False

        # 确定文件名
        if args and len(args) > 0:
            filename = args[0]
            if not filename.endswith('.session'):
                filename += '.session'
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.patient_id}_{timestamp}.session"

        filepath = os.path.join(self.save_dir, filename)

        try:
            self.agent.save_state(filepath)
            self.session_file = filepath
            print(f"✓ 会话已保存到: {filepath}")
        except Exception as e:
            print(f"✗ 保存失败: {e}")

        return False

    def _cmd_load(self, args: List[str] = None) -> bool:
        """加载会话状态"""
        if not args:
            print("! 请指定要加载的文件名")
            print("  用法: /load <文件名>")
            return False

        filename = args[0]
        if not filename.endswith('.session'):
            filename += '.session'

        filepath = os.path.join(self.save_dir, filename)

        if not os.path.exists(filepath):
            print(f"! 文件不存在: {filepath}")
            # 显示可用文件
            files = [f for f in os.listdir(self.save_dir) if f.endswith('.session')]
            if files:
                print("可用会话文件:")
                for f in files[:10]:  # 最多显示10个
                    print(f"  {f}")
            return False

        try:
            if not self.agent:
                from core.agent import MedicalAgent
                self.agent = MedicalAgent()

            success = self.agent.load_state(filepath)
            if success:
                self.session_file = filepath
                self.patient_id = self.agent.patient_id or self.patient_id
                print(f"✓ 会话已从 {filename} 加载")
                print(f"  患者ID: {self.patient_id}")

                # 显示最后几步
                last_steps = self.agent.get_last_steps()
                if last_steps:
                    print(f"  历史步骤: {len(last_steps)}步")
            else:
                print("✗ 加载失败")
        except Exception as e:
            print(f"✗ 加载失败: {e}")

        return False

    def _cmd_status(self, args: List[str] = None) -> bool:
        """显示当前会话状态"""
        print("\n" + "=" * 60)
        print("会话状态")
        print("=" * 60)

        print(f"患者ID: {self.patient_id}")
        print(f"会话文件: {self.session_file or '未保存'}")

        if self.agent:
            # 显示工作流状态
            workflow = self.agent.get_workflow_state(self.patient_id)
            if workflow:
                print(f"工作流步骤: {workflow.get('current_step', '未开始')}")
                print(f"工作流数据: {len(workflow.get('data', {}))} 条记录")

            # 显示审批ID
            approval_id = self.agent.get_approval_id()
            if approval_id:
                print(f"审批ID: {approval_id}")

            # 显示最后步骤数
            last_steps = self.agent.get_last_steps()
            print(f"最后对话步骤: {len(last_steps)}步")
        else:
            print("Agent: 未初始化")

        print("=" * 60)
        return False

    def _cmd_history(self, args: List[str] = None) -> bool:
        """显示命令历史"""
        print("\n命令历史:")
        for i, cmd in enumerate(self.command_history[-20:], 1):  # 显示最后20条
            print(f"  {i:2d}. {cmd}")
        return False

    def _cmd_workflow(self, args: List[str] = None) -> bool:
        """显示工作流状态"""
        if not self.agent:
            print("! Agent未初始化")
            return False

        workflow = self.agent.get_workflow_state(self.patient_id)
        if not workflow:
            print("! 未找到工作流状态")
            return False

        print("\n" + "=" * 60)
        print("工作流状态")
        print("=" * 60)

        print(f"患者ID: {workflow.get('patient_id')}")
        print(f"当前步骤: {workflow.get('current_step')}")
        print(f"创建时间: {workflow.get('created_at')}")
        print(f"更新时间: {workflow.get('updated_at')}")

        data = workflow.get('data', {})
        if data:
            print("\n工作流数据:")
            for step, step_data in data.items():
                print(f"  {step}:")
                if isinstance(step_data, dict):
                    for key, value in step_data.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"    {key}: {value[:100]}...")
                        else:
                            print(f"    {key}: {value}")
                else:
                    print(f"    {step_data}")

        print("=" * 60)
        return False

    def _cmd_stats(self, args: List[str] = None) -> bool:
        """显示统计信息"""
        from llm.client import LLMClient

        print("\n" + "=" * 60)
        print("系统统计")
        print("=" * 60)

        # LLM统计
        llm_stats = LLMClient.get_stats()
        print("LLM API调用:")
        print(f"  请求次数: {llm_stats.get('requests', 0)}")
        print(f"  估算tokens: {llm_stats.get('estimated_tokens', 0)}")

        # 工作流统计
        if self.agent:
            workflow_stats = self.agent.get_workflow_stats()
            print("\n工作流统计:")
            print(f"  活跃工作流: {workflow_stats.get('active_workflows', 0)}")
            print(f"  完成工作流: {workflow_stats.get('completed_workflows', 0)}")
            print(f"  总工作流: {workflow_stats.get('total_workflows', 0)}")

        # 会话统计
        if os.path.exists(self.save_dir):
            session_files = [f for f in os.listdir(self.save_dir) if f.endswith('.session')]
            print(f"\n会话文件: {len(session_files)}个")

        print("=" * 60)
        return False

    def _cmd_exit(self, args: List[str] = None) -> bool:
        """退出程序"""
        print("\n正在退出...")

        # 询问是否保存
        if self.agent and self.agent.get_last_steps():
            save = input("\n退出前是否保存当前会话？(y/n): ").strip().lower()
            if save == 'y':
                self._cmd_save()

        print("再见！")
        return True  # 退出

    def _cmd_clear(self, args: List[str] = None) -> bool:
        """清空屏幕"""
        os.system('clear' if os.name == 'posix' else 'cls')
        self._print_banner()
        return False

    def _cmd_patient(self, args: List[str] = None) -> bool:
        """查看或更改患者ID"""
        if args and len(args) > 0:
            new_id = args[0]
            old_id = self.patient_id
            self.patient_id = new_id

            # 如果Agent已初始化，更新patient_id
            if self.agent:
                self.agent.patient_id = new_id

            print(f"✓ 患者ID已更改: {old_id} → {new_id}")

            # 询问是否保存当前会话
            if self.agent and self.agent.get_last_steps():
                save = input("是否保存当前会话状态？(y/n): ").strip().lower()
                if save == 'y':
                    self._cmd_save()
        else:
            print(f"当前患者ID: {self.patient_id}")

        return False

    def _process_input(self, user_input: str) -> bool:
        """处理用户输入"""
        user_input = user_input.strip()

        # 记录命令历史
        self.command_history.append(user_input)

        # 检查是否是特殊命令
        if user_input.startswith('/'):
            parts = user_input.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd in self.commands:
                return self.commands[cmd](args)
            else:
                print(f"! 未知命令: {cmd}")
                print("  输入 '/help' 查看可用命令")
                return False

        # 普通用户输入 - 处理医疗咨询
        if not user_input:
            return False

        print(f"\n[您] {user_input}")

        # 确保Agent已初始化
        if not self.agent:
            try:
                from core.agent import MedicalAgent
                print("正在初始化MedicalAgent...")
                self.agent = MedicalAgent()
                print("✓ Agent初始化完成")
            except Exception as e:
                print(f"✗ Agent初始化失败: {e}")
                return False

        # 处理用户输入
        try:
            response, steps = self.agent.run(user_input, patient_id=self.patient_id)

            # 显示响应
            print(f"\n[助手] {response}")

            # 显示工具调用详情（如果有）
            tool_steps = [s for s in steps if s.get('type') == 'tool_call']
            if tool_steps:
                print(f"\n[工具调用] {len(tool_steps)}次调用:")
                for ts in tool_steps:
                    tool_name = ts.get('tool', '未知')
                    duration = ts.get('duration_ms', 0)
                    result = str(ts.get('result', '无结果'))

                    if len(result) > 100:
                        result = result[:100] + "..."

                    print(f"  - {tool_name} ({duration}ms): {result}")

            # 显示步骤统计
            print(f"\n[统计] 本次处理使用了 {len(steps)} 个步骤")

        except Exception as e:
            print(f"✗ 处理失败: {e}")
            logger.exception("详细错误信息")

        return False

    def run(self) -> None:
        """运行交互式CLI"""
        self._print_banner()

        # 尝试初始化Agent
        try:
            from core.agent import MedicalAgent
            self.agent = MedicalAgent()
            print("✓ MedicalAgent初始化成功")
        except Exception as e:
            print(f"! Agent初始化失败: {e}")
            print("请检查配置和依赖")
            print("可以继续尝试使用，某些功能可能受限")

        # 主循环
        while True:
            try:
                # 显示提示符
                prompt = f"\n[{self.patient_id}]> "
                user_input = input(prompt).strip()

                # 处理输入
                should_exit = self._process_input(user_input)
                if should_exit:
                    break

            except KeyboardInterrupt:
                print("\n\n检测到Ctrl+C，输入 '/exit' 退出程序")
                print("或直接按Enter继续")
            except EOFError:
                print("\n\n检测到EOF，退出程序")
                break
            except Exception as e:
                print(f"\n! 处理输入时发生错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='P1医疗用药助手 - 交互式命令行界面')
    parser.add_argument('patient_id', nargs='?', help='患者ID（可选）')
    parser.add_argument('--save-dir', default='./sessions', help='会话保存目录（默认: ./sessions）')
    parser.add_argument('--version', action='version', version='P1医疗助手CLI v1.0')

    args = parser.parse_args()

    # 创建并运行CLI
    try:
        cli = InteractiveCLI(
            patient_id=args.patient_id,
            save_dir=args.save_dir
        )
        cli.run()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()