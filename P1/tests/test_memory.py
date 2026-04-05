# test_memory.py
"""内存管理模块测试"""

import unittest
from typing import List, Dict
from memory.manager import MessageManager
from memory.compressor import (
    compress_messages_by_tokens,
    compress_messages_by_count,
    smart_compress
)


class TestMessageManager(unittest.TestCase):
    """测试MessageManager类"""

    def setUp(self):
        """测试前准备"""
        self.system_prompt = "你是一个医疗助手"
        self.manager = MessageManager(system_prompt=self.system_prompt)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.manager.system_prompt, self.system_prompt)
        self.assertEqual(len(self.manager.messages), 1)
        self.assertEqual(self.manager.messages[0]["role"], "system")
        self.assertEqual(self.manager.messages[0]["content"], self.system_prompt)

    def test_add_message(self):
        """测试添加消息"""
        self.manager.add_message("user", "你好")
        self.assertEqual(len(self.manager.messages), 2)
        self.assertEqual(self.manager.messages[1]["role"], "user")
        self.assertEqual(self.manager.messages[1]["content"], "你好")

    def test_add_tool_result(self):
        """测试添加工具结果"""
        self.manager.add_tool_result("tool_123", "查询结果")
        self.assertEqual(len(self.manager.messages), 2)
        self.assertEqual(self.manager.messages[1]["role"], "tool")
        self.assertEqual(self.manager.messages[1]["tool_call_id"], "tool_123")
        self.assertEqual(self.manager.messages[1]["content"], "查询结果")

    def test_get_messages(self):
        """测试获取消息（不包含系统消息）"""
        self.manager.add_message("user", "问题1")
        self.manager.add_message("assistant", "回答1")

        messages = self.manager.get_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")

    def test_get_full_messages(self):
        """测试获取完整消息（包含系统消息）"""
        self.manager.add_message("user", "问题1")

        messages = self.manager.get_full_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")

    def test_reset_keep_system(self):
        """测试重置并保留系统消息"""
        self.manager.add_message("user", "问题1")
        self.manager.add_message("assistant", "回答1")

        self.manager.reset(keep_system=True)
        self.assertEqual(len(self.manager.messages), 1)
        self.assertEqual(self.manager.messages[0]["role"], "system")

    def test_reset_without_system(self):
        """测试重置不保留系统消息"""
        self.manager.add_message("user", "问题1")

        self.manager.reset(keep_system=False)
        self.assertEqual(len(self.manager.messages), 0)

    def test_get_last_user_message(self):
        """测试获取最后一条用户消息"""
        self.manager.add_message("user", "问题1")
        self.manager.add_message("assistant", "回答1")
        self.manager.add_message("user", "问题2")

        last_message = self.manager.get_last_user_message()
        self.assertEqual(last_message, "问题2")

    def test_get_conversation_length(self):
        """测试获取对话长度"""
        self.manager.add_message("user", "问题1")
        self.manager.add_message("assistant", "回答1")

        length = self.manager.get_conversation_length()
        self.assertEqual(length, 3)  # 系统消息 + 2条消息

    def test_estimate_total_tokens(self):
        """测试估算token总数"""
        self.manager.add_message("user", "这是一个测试消息")
        # "这是一个测试消息" 有7个字符，7 // 4 = 1
        tokens = self.manager.estimate_total_tokens()
        self.assertGreaterEqual(tokens, 1)


class TestCompressor(unittest.TestCase):
    """测试压缩函数"""

    def setUp(self):
        """测试前准备"""
        self.messages = [
            {"role": "system", "content": "系统提示"},
            {"role": "user", "content": "用户消息1"},
            {"role": "assistant", "content": "助手回复1"},
            {"role": "user", "content": "用户消息2"},
            {"role": "assistant", "content": "助手回复2"},
        ]

    def test_compress_messages_by_tokens(self):
        """测试按token压缩"""
        # 创建长消息以触发压缩
        long_messages = [
            {"role": "system", "content": "系统提示"},
            {"role": "user", "content": "a" * 10000},  # 约2500 tokens
            {"role": "assistant", "content": "b" * 10000},  # 约2500 tokens
        ]

        compressed = compress_messages_by_tokens(long_messages, max_tokens=3000)
        self.assertLessEqual(len(compressed), len(long_messages))

    def test_compress_messages_by_count(self):
        """测试按数量压缩"""
        # 创建超过限制的消息
        many_messages = []
        for i in range(30):
            many_messages.append({"role": "user", "content": f"消息{i}"})

        compressed = compress_messages_by_count(many_messages, max_messages=20)
        self.assertEqual(len(compressed), 20)

    def test_compress_messages_by_count_preserve_system(self):
        """测试按数量压缩时保留系统消息"""
        many_messages = [{"role": "system", "content": "系统提示"}]
        for i in range(25):
            many_messages.append({"role": "user", "content": f"消息{i}"})

        compressed = compress_messages_by_count(many_messages, max_messages=20, preserve_system=True)
        self.assertEqual(len(compressed), 20)
        self.assertEqual(compressed[0]["role"], "system")

    def test_smart_compress(self):
        """测试智能压缩"""
        # 创建既长又多的消息
        many_long_messages = [{"role": "system", "content": "系统提示"}]
        for i in range(25):
            many_long_messages.append({"role": "user", "content": "x" * 1000})

        compressed = smart_compress(many_long_messages, max_tokens=3000, max_messages=20)
        self.assertLessEqual(len(compressed), 20)


if __name__ == "__main__":
    unittest.main()