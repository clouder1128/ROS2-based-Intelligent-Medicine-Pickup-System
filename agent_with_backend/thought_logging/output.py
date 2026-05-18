# agent_with_backend/P1/thought_logging/output.py
import os
import json
import logging
from typing import Dict, Any, Optional, List
from .config import ThoughtLoggingConfig
from .utils import safe_json_dumps, ensure_directory, format_timestamp

logger = logging.getLogger(__name__)


class JSONFileWriter:
    """JSON文件写入器"""

    def __init__(self, log_dir: str):
        """
        初始化JSON文件写入器

        参数:
            log_dir: 日志目录路径
        """
        self.log_dir = log_dir
        logger.debug(f"初始化JSONFileWriter，日志目录: {log_dir}")

    def write_thought(self, thought: Dict[str, Any]) -> bool:
        """
        写入思考记录到JSON文件

        参数:
            thought: 思考记录字典

        返回:
            bool: 写入是否成功
        """
        try:
            # 获取会话ID
            session_id = thought.get("session_id")
            if not session_id:
                logger.warning("思考记录缺少session_id，跳过写入")
                return False

            # 创建会话目录
            session_dir = os.path.join(self.log_dir, session_id)
            if not ensure_directory(session_dir):
                logger.error(f"无法创建会话目录: {session_dir}")
                return False

            # JSON文件路径
            json_file = os.path.join(session_dir, "thoughts.json")

            # 读取现有数据或创建新列表
            existing_data = []
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = [existing_data]
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"读取现有JSON文件失败，创建新文件: {e}")
                    existing_data = []

            # 添加新记录
            existing_data.append(thought)

            # 写入文件
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"成功写入JSON记录到: {json_file}")
            return True

        except Exception as e:
            logger.error(f"写入JSON文件失败: {e}")
            return False


class TextFileWriter:
    """文本文件写入器（人类可读格式）"""

    def __init__(self, log_dir: str):
        """
        初始化文本文件写入器

        参数:
            log_dir: 日志目录路径
        """
        self.log_dir = log_dir
        logger.debug(f"初始化TextFileWriter，日志目录: {log_dir}")

    def write_thought(self, thought: Dict[str, Any]) -> bool:
        """
        写入思考记录到文本文件

        参数:
            thought: 思考记录字典

        返回:
            bool: 写入是否成功
        """
        try:
            # 获取会话ID
            session_id = thought.get("session_id")
            if not session_id:
                logger.warning("思考记录缺少session_id，跳过写入")
                return False

            # 创建会话目录
            session_dir = os.path.join(self.log_dir, session_id)
            if not ensure_directory(session_dir):
                logger.error(f"无法创建会话目录: {session_dir}")
                return False

            # 文本文件路径
            text_file = os.path.join(session_dir, "thoughts.log")

            # 格式化文本内容
            formatted_text = self._format_thought(thought)

            # 写入文件（追加模式）
            with open(text_file, 'a', encoding='utf-8') as f:
                f.write(formatted_text)
                f.write("\n" + "=" * 80 + "\n\n")

            logger.debug(f"成功写入文本记录到: {text_file}")
            return True

        except Exception as e:
            logger.error(f"写入文本文件失败: {e}")
            return False

    def _format_thought(self, thought: Dict[str, Any]) -> str:
        """
        格式化思考记录为人类可读文本

        参数:
            thought: 思考记录字典

        返回:
            str: 格式化后的文本
        """
        thought_type = thought.get("type", "unknown")
        timestamp = thought.get("timestamp")
        formatted_timestamp = thought.get("formatted_timestamp") or format_timestamp(timestamp)
        session_id = thought.get("session_id", "unknown")
        iteration = thought.get("iteration", 0)

        # 构建基础信息
        lines = [
            f"思考类型: {thought_type}",
            f"时间: {formatted_timestamp}",
            f"会话ID: {session_id}",
            f"迭代: {iteration}",
            ""
        ]

        # 根据类型添加详细信息
        if thought_type == "llm_call":
            lines.extend(self._format_llm_call(thought))
        elif thought_type == "tool_decision":
            lines.extend(self._format_tool_decision(thought))
        elif thought_type == "tool_result":
            lines.extend(self._format_tool_result(thought))
        elif thought_type == "error":
            lines.extend(self._format_error(thought))
        else:
            # 通用格式
            for key, value in thought.items():
                if key not in ["type", "timestamp", "formatted_timestamp", "session_id", "iteration"]:
                    lines.append(f"{key}: {self._format_value(value)}")

        return "\n".join(lines)

    def _format_llm_call(self, thought: Dict[str, Any]) -> List[str]:
        """格式化LLM调用记录"""
        lines = ["LLM Call Details:"]
        messages = thought.get("messages", [])
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"  [{i+1}] {role}: {self._truncate_text(content, 200)}")

        response = thought.get("response", {})
        if response:
            lines.append("")
            lines.append("LLM Response:")
            lines.append(f"  {self._truncate_text(str(response), 300)}")

        return lines

    def _format_tool_decision(self, thought: Dict[str, Any]) -> List[str]:
        """格式化工具决策记录"""
        lines = ["Tool Decision Details:"]
        tool_name = thought.get("tool_name", "unknown")
        tool_args = thought.get("tool_args", {})
        reason = thought.get("reason", "")

        lines.append(f"  Tool Name: {tool_name}")
        if tool_args:
            lines.append(f"  Tool Arguments: {self._format_value(tool_args)}")
        if reason:
            lines.append(f"  Decision Reason: {reason}")

        return lines

    def _format_tool_result(self, thought: Dict[str, Any]) -> List[str]:
        """格式化工具结果记录"""
        lines = ["Tool Execution Result:"]
        tool_name = thought.get("tool_name", "unknown")
        success = thought.get("success", False)
        result = thought.get("result", {})

        lines.append(f"  Tool Name: {tool_name}")
        lines.append(f"  Execution Success: {success}")
        if result:
            lines.append(f"  Execution Result: {self._format_value(result)}")

        error = thought.get("error")
        if error:
            lines.append(f"  Error Message: {error}")

        return lines

    def _format_error(self, thought: Dict[str, Any]) -> List[str]:
        """格式化错误记录"""
        lines = ["Error Details:"]
        error_msg = thought.get("error_message", "Unknown error")
        error_type = thought.get("error_type", "unknown")
        stack_trace = thought.get("stack_trace", "")

        lines.append(f"  Error Type: {error_type}")
        lines.append(f"  Error Message: {error_msg}")
        if stack_trace:
            lines.append(f"  Stack Trace: {stack_trace}")

        return lines

    def _format_value(self, value: Any, indent: int = 0) -> str:
        """格式化值"""
        if isinstance(value, dict):
            lines = []
            for k, v in value.items():
                lines.append(f"{'  ' * indent}{k}: {self._format_value(v, indent + 1)}")
            return "\n".join(lines)
        elif isinstance(value, list):
            if len(value) == 0:
                return "[]"
            lines = []
            for i, item in enumerate(value):
                lines.append(f"{'  ' * indent}[{i}]: {self._format_value(item, indent + 1)}")
            return "\n".join(lines)
        else:
            return str(value)

    def _truncate_text(self, text: str, max_length: int = 200) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."


class TerminalLogger:
    """终端日志记录器（实时输出）"""

    def __init__(self, enabled: bool = False):
        """
        初始化终端日志记录器

        参数:
            enabled: 是否启用终端日志
        """
        self.enabled = enabled
        logger.debug(f"初始化TerminalLogger，启用状态: {enabled}")

    def log(self, thought: Dict[str, Any]) -> None:
        """
        在终端输出思考记录

        参数:
            thought: 思考记录字典
        """
        if not self.enabled:
            return

        try:
            thought_type = thought.get("type", "unknown")
            iteration = thought.get("iteration", 0)
            timestamp = thought.get("formatted_timestamp") or format_timestamp(thought.get("timestamp"))

            # 根据类型选择颜色和前缀
            if thought_type == "llm_call":
                prefix = "🤖 LLM Call"
                color = "\033[94m"  # 蓝色
            elif thought_type == "tool_decision":
                prefix = "🔧 Tool Decision"
                color = "\033[93m"  # 黄色
            elif thought_type == "tool_result":
                success = thought.get("success", False)
                prefix = "✅ Tool Result" if success else "❌ Tool Result"
                color = "\033[92m" if success else "\033[91m"  # 绿色/红色
            elif thought_type == "error":
                prefix = "💥 Error"
                color = "\033[91m"  # 红色
            else:
                prefix = "📝 Thought"
                color = "\033[96m"  # 青色

            reset = "\033[0m"

            # 构建输出行
            output = f"{color}{prefix} [{iteration}] {timestamp}{reset}"

            # 添加额外信息
            if thought_type == "tool_decision":
                tool_name = thought.get("tool_name", "unknown")
                output += f" - {tool_name}"
            elif thought_type == "llm_call":
                messages = thought.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    role = last_msg.get("role", "unknown")
                    content = last_msg.get("content", "")
                    truncated = self._truncate_for_terminal(content, 50)
                    output += f" - {role}: {truncated}"

            print(output)

        except Exception as e:
            logger.error(f"终端日志输出失败: {e}")

    def _truncate_for_terminal(self, text: str, max_length: int = 50) -> str:
        """为终端显示截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."


class OutputManager:
    """输出管理器，协调不同格式的输出"""

    def __init__(self, config: ThoughtLoggingConfig):
        """
        初始化输出管理器

        参数:
            config: 思考记录配置
        """
        self.config = config
        self.json_writer: Optional[JSONFileWriter] = None
        self.text_writer: Optional[TextFileWriter] = None
        self.terminal_logger: Optional[TerminalLogger] = None

        self._initialize_writers()
        logger.debug(f"初始化OutputManager，配置: {config.to_dict()}")

    def _initialize_writers(self) -> None:
        """初始化写入器"""
        # 初始化终端日志记录器
        self.terminal_logger = TerminalLogger(enabled=self.config.log_to_console)

        # 如果启用文件日志，初始化文件写入器
        if self.config.log_to_file:
            log_dir = self.config.log_dir

            # 初始化JSON写入器（如果配置中包含json格式）
            if "json" in self.config.log_formats:
                self.json_writer = JSONFileWriter(log_dir)

            # 初始化文本写入器（如果配置中包含text格式）
            if "text" in self.config.log_formats:
                self.text_writer = TextFileWriter(log_dir)

    def write_thought(self, thought: Dict[str, Any]) -> bool:
        """
        写入思考记录到所有启用的输出

        参数:
            thought: 思考记录字典

        返回:
            bool: 是否至少有一个输出成功
        """
        if not self.config.enabled:
            logger.debug("思考记录功能已禁用，跳过写入")
            return False

        success = False

        # 写入JSON文件
        if self.json_writer:
            if self.json_writer.write_thought(thought):
                success = True
            else:
                logger.warning("JSON文件写入失败")

        # 写入文本文件
        if self.text_writer:
            if self.text_writer.write_thought(thought):
                success = True
            else:
                logger.warning("文本文件写入失败")

        # 输出到终端
        if self.terminal_logger and self.terminal_logger.enabled:
            self.terminal_logger.log(thought)
            success = True  # 终端输出总是视为成功

        return success

    def cleanup(self) -> None:
        """清理资源"""
        logger.debug("清理OutputManager资源")
        # 目前没有需要清理的资源