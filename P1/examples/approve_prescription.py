#!/usr/bin/env python3
"""
医生审批系统 - 交互式命令行界面
支持多次操作、添加医生建议、批准/拒绝审批单
"""

import sys
import os
import json
import httpx
import readline  # 用于命令行历史记录
from typing import Optional, List, Dict, Any


class DoctorCLI:
    """医生交互式命令行界面"""

    def __init__(self, doctor_id: str = "doctor_test_001"):
        """
        初始化医生CLI

        Args:
            doctor_id: 医生ID，默认为测试医生
        """
        self.doctor_id = doctor_id
        self.command_history: List[str] = []

        # 命令映射
        self.commands = {
            "/help": self._cmd_help,
            "/list": self._cmd_list,
            "/approve": self._cmd_approve,
            "/reject": self._cmd_reject,
            "/view": self._cmd_view,
            "/status": self._cmd_status,
            "/orders": self._cmd_orders,
            "/exit": self._cmd_exit,
            "/quit": self._cmd_exit,
            "/clear": self._cmd_clear,
            "/doctor": self._cmd_doctor,
        }

    def _print_banner(self) -> None:
        """打印欢迎横幅"""
        print("\n" + "=" * 60)
        print("医生审批系统 - 交互式命令行界面")
        print("=" * 60)
        print(f"医生ID: {self.doctor_id}")
        print("输入 '/help' 查看可用命令")
        print("输入 '/exit' 退出程序")
        print("=" * 60 + "\n")

    def _cmd_help(self, args: List[str] = None) -> bool:
        """显示帮助信息"""
        print("\n" + "=" * 60)
        print("可用命令:")
        print("=" * 60)
        print("  /help                - 显示此帮助信息")
        print("  /list                - 列出所有待审批的审批单")
        print("  /approve [ID]        - 批准指定审批单（可输入医生建议）")
        print("  /reject [ID]         - 拒绝指定审批单（需输入拒绝理由）")
        print("  /view [ID]           - 查看审批单详细信息")
        print("  /status [ID]         - 检查审批单状态")
        print("  /orders              - 查看订单/库存扣减情况")
        print("  /doctor [新ID]       - 查看或更改医生ID")
        print("  /clear               - 清空屏幕")
        print("  /exit, /quit         - 退出程序")
        print("\n常规使用:")
        print("  1. 输入 /list 查看待审批的审批单")
        print("  2. 输入 /approve 1 批准第1个审批单")
        print("  3. 系统会提示输入医生建议（可选）")
        print("  4. 审批通过后自动扣减库存并创建订单")
        print("=" * 60)
        return False

    def _cmd_list(self, args: List[str] = None) -> bool:
        """列出所有待审批的审批单"""
        print("正在获取审批单列表...")
        try:
            response = httpx.get("http://localhost:8001/api/approvals/pending", timeout=10)
            if response.status_code == 200:
                data = response.json()
                approvals = data.get("approvals", [])
                if not approvals:
                    print("暂无待审批的审批单")
                    return False

                print(f"\n待审批的审批单 ({len(approvals)}个):")
                for i, approval in enumerate(approvals, 1):
                    print(f"{i}. ID: {approval.get('approval_id', approval.get('id', '未知'))}")
                    print(f"   患者: {approval.get('patient_name')}")
                    print(f"   症状: {approval.get('symptoms', '无')}")
                    print(f"   状态: {approval.get('status', '未知')}")
                    print(f"   创建时间: {approval.get('created_at', '未知')}")
                    # 显示药品信息（如果有）
                    drug_name = approval.get('drug_name')
                    if drug_name:
                        print(f"   药品: {drug_name}")
                        quantity = approval.get('quantity', 1)
                        print(f"   数量: {quantity}")
                    print()
                return False
            else:
                print(f"获取审批单失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"获取审批单出错: {e}")
            return False

    def _cmd_approve(self, args: List[str] = None) -> bool:
        """批准审批单

        用法: /approve [审批单编号或ID]
        示例: /approve 1      (批准列表中的第1个审批单)
              /approve AP-20260408-ABCD1234 (直接批准指定ID)
        """
        approval_id = None

        if not args:
            # 如果没有参数，先列出待审批单让用户选择
            approvals = self._get_pending_approvals()
            if not approvals:
                print("没有待审批的审批单")
                return False

            try:
                choice = input("\n请输入要批准的审批单编号 (1, 2, 3...) 或输入审批ID: ").strip()
                if not choice:
                    print("操作取消")
                    return False

                # 检查是否是数字（列表索引）
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(approvals):
                        approval_id = approvals[idx].get("approval_id", approvals[idx].get("id"))
                    else:
                        print("无效的编号")
                        return False
                else:
                    # 直接使用输入的ID
                    approval_id = choice
            except (ValueError, IndexError):
                print("无效的输入")
                return False
            except KeyboardInterrupt:
                print("\n操作取消")
                return False
        else:
            # 有参数，可能是编号或ID
            arg = args[0]
            if arg.isdigit():
                # 数字，从列表中获取
                approvals = self._get_pending_approvals()
                if not approvals:
                    print("没有待审批的审批单")
                    return False

                idx = int(arg) - 1
                if 0 <= idx < len(approvals):
                    approval_id = approvals[idx].get("approval_id", approvals[idx].get("id"))
                else:
                    print(f"无效的编号: {arg}，有效范围: 1-{len(approvals)}")
                    return False
            else:
                # 直接使用ID
                approval_id = arg

        if not approval_id:
            print("未指定审批ID")
            return False

        print(f"正在批准审批单: {approval_id}")

        # 询问医生建议（可选）
        doctor_notes = None
        try:
            notes_input = input("\n请输入医生建议（可选，直接按Enter跳过）: ").strip()
            if notes_input:
                doctor_notes = notes_input
                print(f"已记录医生建议: {notes_input[:50]}...")
        except KeyboardInterrupt:
            print("\n跳过医生建议输入")

        # 批准请求数据
        payload = {
            "doctor_id": self.doctor_id
        }
        if doctor_notes:
            payload["notes"] = doctor_notes

        try:
            url = f"http://localhost:8001/api/approvals/{approval_id}/approve"
            response = httpx.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ 审批批准成功!")
                print(f"   审批ID: {result.get('approval_id')}")
                print(f"   批准医生: {result.get('doctor_id', self.doctor_id)}")
                print(f"   批准时间: {result.get('approved_at', '刚刚')}")

                if doctor_notes:
                    print(f"   医生建议: {doctor_notes[:100]}...")

                # 显示订单创建状态
                if result.get('order_created'):
                    print(f"   📦 订单创建: {result.get('order_message', '成功')}")
                    if result.get('task_id'):
                        print(f"   任务ID: {result.get('task_id')}")
                else:
                    print(f"   ⚠ 订单创建: {result.get('order_message', '未创建')}")

                # 检查订单详情
                self._check_orders()
                return False
            else:
                print(f"❌ 审批批准失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 批准审批单出错: {e}")
            return False

    def _cmd_reject(self, args: List[str] = None) -> bool:
        """拒绝审批单

        用法: /reject [审批单编号或ID]
        示例: /reject 1      (拒绝列表中的第1个审批单)
              /reject AP-20260408-ABCD1234 (直接拒绝指定ID)
        """
        approval_id = None

        if not args:
            # 如果没有参数，先列出待审批单让用户选择
            approvals = self._get_pending_approvals()
            if not approvals:
                print("没有待审批的审批单")
                return False

            try:
                choice = input("\n请输入要拒绝的审批单编号 (1, 2, 3...) 或输入审批ID: ").strip()
                if not choice:
                    print("操作取消")
                    return False

                # 检查是否是数字（列表索引）
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(approvals):
                        approval_id = approvals[idx].get("approval_id", approvals[idx].get("id"))
                    else:
                        print("无效的编号")
                        return False
                else:
                    # 直接使用输入的ID
                    approval_id = choice
            except (ValueError, IndexError):
                print("无效的输入")
                return False
            except KeyboardInterrupt:
                print("\n操作取消")
                return False
        else:
            # 有参数，可能是编号或ID
            arg = args[0]
            if arg.isdigit():
                # 数字，从列表中获取
                approvals = self._get_pending_approvals()
                if not approvals:
                    print("没有待审批的审批单")
                    return False

                idx = int(arg) - 1
                if 0 <= idx < len(approvals):
                    approval_id = approvals[idx].get("approval_id", approvals[idx].get("id"))
                else:
                    print(f"无效的编号: {arg}，有效范围: 1-{len(approvals)}")
                    return False
            else:
                # 直接使用ID
                approval_id = arg

        if not approval_id:
            print("未指定审批ID")
            return False

        print(f"正在拒绝审批单: {approval_id}")

        # 要求输入拒绝理由
        reject_reason = None
        try:
            while not reject_reason:
                reason_input = input("\n请输入拒绝理由（必填）: ").strip()
                if reason_input:
                    reject_reason = reason_input
                else:
                    print("拒绝理由不能为空，请重新输入")
        except KeyboardInterrupt:
            print("\n操作取消")
            return False

        # 拒绝请求数据
        payload = {
            "doctor_id": self.doctor_id,
            "reason": reject_reason
        }

        try:
            url = f"http://localhost:8001/api/approvals/{approval_id}/reject"
            response = httpx.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ 审批拒绝成功!")
                print(f"   审批ID: {result.get('approval_id')}")
                print(f"   拒绝医生: {result.get('doctor_id', self.doctor_id)}")
                print(f"   拒绝时间: {result.get('rejected_at', '刚刚')}")
                print(f"   拒绝理由: {reject_reason[:100]}...")
                return False
            else:
                print(f"❌ 审批拒绝失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 拒绝审批单出错: {e}")
            return False

    def _cmd_view(self, args: List[str] = None) -> bool:
        """查看审批单详细信息

        用法: /view [审批单编号或ID]
        示例: /view 1      (查看列表中的第1个审批单)
              /view AP-20260408-ABCD1234 (查看指定ID)
        """
        approval_id = None

        if not args:
            # 如果没有参数，先列出待审批单让用户选择
            approvals = self._get_pending_approvals()
            if not approvals:
                print("没有待审批的审批单")
                # 尝试获取所有审批单
                return False

            try:
                choice = input("\n请输入要查看的审批单编号 (1, 2, 3...) 或输入审批ID: ").strip()
                if not choice:
                    print("操作取消")
                    return False

                # 检查是否是数字（列表索引）
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(approvals):
                        approval_id = approvals[idx].get("approval_id", approvals[idx].get("id"))
                    else:
                        print("无效的编号")
                        return False
                else:
                    # 直接使用输入的ID
                    approval_id = choice
            except (ValueError, IndexError):
                print("无效的输入")
                return False
            except KeyboardInterrupt:
                print("\n操作取消")
                return False
        else:
            # 有参数，可能是编号或ID
            arg = args[0]
            if arg.isdigit():
                # 数字，从列表中获取
                approvals = self._get_pending_approvals()
                if not approvals:
                    print("没有待审批的审批单")
                    return False

                idx = int(arg) - 1
                if 0 <= idx < len(approvals):
                    approval_id = approvals[idx].get("approval_id", approvals[idx].get("id"))
                else:
                    print(f"无效的编号: {arg}，有效范围: 1-{len(approvals)}")
                    return False
            else:
                # 直接使用ID
                approval_id = arg

        if not approval_id:
            print("未指定审批ID")
            return False

        return self._check_approval_status(approval_id, show_details=True)

    def _cmd_status(self, args: List[str] = None) -> bool:
        """检查审批单状态

        用法: /status [审批单ID]
        示例: /status AP-20260408-ABCD1234
        """
        if not args:
            print("请指定审批单ID")
            print("用法: /status AP-20260408-ABCD1234")
            return False

        approval_id = args[0]
        return self._check_approval_status(approval_id)

    def _cmd_orders(self, args: List[str] = None) -> bool:
        """查看订单/库存扣减情况"""
        return self._check_orders()

    def _cmd_exit(self, args: List[str] = None) -> bool:
        """退出程序"""
        print("\n正在退出医生审批系统...")
        print("再见！")
        return True

    def _cmd_clear(self, args: List[str] = None) -> bool:
        """清空屏幕"""
        os.system('clear' if os.name == 'posix' else 'cls')
        self._print_banner()
        return False

    def _cmd_doctor(self, args: List[str] = None) -> bool:
        """查看或更改医生ID"""
        if args and len(args) > 0:
            new_id = args[0]
            old_id = self.doctor_id
            self.doctor_id = new_id
            print(f"✓ 医生ID已更改: {old_id} → {new_id}")
        else:
            print(f"当前医生ID: {self.doctor_id}")
        return False

    def _get_pending_approvals(self) -> List[Dict[str, Any]]:
        """获取待审批的审批单列表"""
        try:
            response = httpx.get("http://localhost:8001/api/approvals/pending", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("approvals", [])
            else:
                print(f"获取审批单失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"获取审批单出错: {e}")
            return []

    def _check_approval_status(self, approval_id: str, show_details: bool = False) -> bool:
        """检查审批单状态"""
        try:
            url = f"http://localhost:8001/api/approvals/{approval_id}"
            response = httpx.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                approval = data.get("approval", {})

                if show_details:
                    print(f"\n📋 审批单详细信息:")
                    print(f"   ID: {approval.get('approval_id')}")
                    print(f"   患者: {approval.get('patient_name')}")
                    print(f"   年龄: {approval.get('patient_age', '未知')}")
                    print(f"   体重: {approval.get('patient_weight', '未知')}kg")
                    print(f"   症状: {approval.get('symptoms', '无')}")

                    drug_name = approval.get('drug_name')
                    if drug_name:
                        print(f"   药品: {drug_name}")
                        quantity = approval.get('quantity', 1)
                        print(f"   数量: {quantity}")

                    status = approval.get('status', 'unknown')
                    status_display = {
                        'pending': '🟡 待审批',
                        'approved': '✅ 已批准',
                        'rejected': '❌ 已拒绝',
                        'unknown': '❓ 未知'
                    }.get(status, f'❓ {status}')
                    print(f"   状态: {status_display}")

                    advice = approval.get('advice', '无')
                    print(f"\n💊 用药建议:")
                    # 显示前200个字符，保留换行
                    advice_preview = advice[:300]
                    if len(advice) > 300:
                        advice_preview += "..."
                    print(f"   {advice_preview.replace(chr(10), chr(10) + '   ')}")

                    print(f"\n📅 时间信息:")
                    print(f"   创建时间: {approval.get('created_at', '未知')}")
                    if status == 'approved':
                        print(f"   批准时间: {approval.get('approved_at', '未批准')}")
                        print(f"   批准医生: {approval.get('doctor_id', '未指定')}")
                    elif status == 'rejected':
                        print(f"   拒绝时间: {approval.get('approved_at', '未拒绝')}")
                        print(f"   拒绝医生: {approval.get('doctor_id', '未指定')}")
                        print(f"   拒绝理由: {approval.get('reject_reason', '无')}")
                else:
                    status = approval.get('status', 'unknown')
                    status_display = {
                        'pending': '🟡 待审批',
                        'approved': '✅ 已批准',
                        'rejected': '❌ 已拒绝',
                        'unknown': '❓ 未知'
                    }.get(status, f'❓ {status}')
                    print(f"\n审批单状态: {status_display}")
                    print(f"患者: {approval.get('patient_name')}")
                    print(f"症状: {approval.get('symptoms', '无')}")
                    print(f"创建时间: {approval.get('created_at', '未知')}")

                return False
            else:
                print(f"获取审批单详情失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"检查审批单状态出错: {e}")
            return False

    def _check_orders(self) -> bool:
        """检查订单/库存扣减情况"""
        try:
            response = httpx.get("http://localhost:8001/api/orders", timeout=10)
            if response.status_code == 200:
                data = response.json()
                orders = data.get("data", [])
                if orders:
                    print(f"\n📦 订单记录 ({len(orders)}个):")
                    for i, order in enumerate(orders[:10], 1):  # 最多显示10个
                        print(f"{i}. 任务ID: {order.get('task_id', '未知')}")
                        print(f"   药品: {order.get('drug_name', '未知')}")
                        print(f"   数量: {order.get('quantity', 0)}")
                        print(f"   状态: {order.get('status', '未知')}")
                        print(f"   创建时间: {order.get('created_at', '未知')}")
                        print()

                    if len(orders) > 10:
                        print(f"... 还有 {len(orders) - 10} 个订单未显示")
                    return False
                else:
                    print("暂无订单记录")
                    return False
            else:
                print(f"获取订单失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"检查订单失败: {e}")
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

        # 普通输入 - 尝试解释为命令
        if not user_input:
            return False

        # 检查是否看起来像审批ID（以AP-开头）
        if user_input.upper().startswith('AP-'):
            print(f"检测到审批ID: {user_input}")
            print("您可以使用以下命令:")
            print(f"  /approve {user_input}  - 批准此审批单")
            print(f"  /view {user_input}     - 查看此审批单详情")
            print(f"  /status {user_input}   - 检查此审批单状态")
            return False

        # 检查是否是数字（可能是列表索引）
        if user_input.isdigit():
            print(f"检测到数字: {user_input}")
            print("您可以使用以下命令:")
            print(f"  /approve {user_input}  - 批准列表中第{user_input}个审批单")
            print(f"  /view {user_input}     - 查看列表中第{user_input}个审批单")
            return False

        print(f"未知输入: {user_input}")
        print("输入 '/help' 查看可用命令")
        return False

    def run(self) -> None:
        """运行交互式CLI"""
        self._print_banner()

        # 检查后端连接
        try:
            response = httpx.get("http://localhost:8001/api/health", timeout=5)
            if response.status_code == 200:
                print("✓ 后端服务连接正常")
            else:
                print(f"⚠ 后端服务连接异常: {response.status_code}")
                print("请确保后端服务正在运行: make backend-start")
        except Exception as e:
            print(f"✗ 无法连接到后端服务: {e}")
            print("请确保后端服务正在运行: make backend-start")
            print("您可以继续尝试，但部分功能可能受限")

        # 主循环
        while True:
            try:
                # 显示提示符
                prompt = f"\n[{self.doctor_id}]> "
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
    """主函数 - 兼容旧版命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(description='医生审批系统 - 交互式命令行界面')
    parser.add_argument('approval_id', nargs='?', help='审批单ID（直接批准模式）')
    parser.add_argument('--doctor-id', default='doctor_test_001', help='医生ID（默认: doctor_test_001）')
    parser.add_argument('--notes', help='医生建议（仅限直接批准模式）')
    parser.add_argument('--version', action='version', version='医生审批系统 v2.0')

    args = parser.parse_args()

    # 如果提供了审批ID，使用直接批准模式（向后兼容）
    if args.approval_id:
        print("医生审批系统 - 直接批准模式")
        print("=" * 60)

        # 使用旧版直接批准逻辑
        import httpx

        payload = {
            "doctor_id": args.doctor_id
        }
        if args.notes:
            payload["notes"] = args.notes

        try:
            url = f"http://localhost:8001/api/approvals/{args.approval_id}/approve"
            response = httpx.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 审批批准成功!")
                print(f"   审批ID: {result.get('approval_id')}")
                print(f"   批准医生: {result.get('doctor_id', args.doctor_id)}")
                print(f"   批准时间: {result.get('approved_at', '刚刚')}")

                if args.notes:
                    print(f"   医生建议: {args.notes[:100]}...")

                # 显示订单创建状态
                if result.get('order_created'):
                    print(f"   📦 订单创建: {result.get('order_message', '成功')}")
                else:
                    print(f"   ⚠ 订单创建: {result.get('order_message', '未创建')}")
            else:
                print(f"❌ 审批批准失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
        except Exception as e:
            print(f"❌ 批准审批单出错: {e}")

        print("\n" + "=" * 60)
        print("提示: 使用交互模式获得更多功能:")
        print("  python approve_prescription.py")
        return

    # 否则，启动交互式CLI
    try:
        cli = DoctorCLI(doctor_id=args.doctor_id)
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
    # 添加一个简单的帮助说明（向后兼容）
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print("用法:")
        print("  1. 交互式模式: python approve_prescription.py")
        print("  2. 直接批准: python approve_prescription.py AP-20260408-ABCD1234")
        print("  3. 带医生建议的直接批准: python approve_prescription.py AP-20260408-ABCD1234 --notes '医生建议内容'")
        print("\n示例:")
        print("  python approve_prescription.py")
        print("  python approve_prescription.py AP-20260408-ABCD1234")
        print("  python approve_prescription.py AP-20260408-ABCD1234 --doctor-id 'doctor_001' --notes '饭后服用'")
        sys.exit(0)

    main()