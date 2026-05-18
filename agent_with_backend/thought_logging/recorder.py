# agent_with_backend/P1/thought_logging/recorder.py
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .config import ThoughtLoggingConfig
from .utils import generate_session_id, format_timestamp, sanitize_for_logging

logger = logging.getLogger(__name__)

@dataclass
class ThoughtRecorder:
    """思考记录器核心类"""

    config: ThoughtLoggingConfig
    enabled: bool = field(init=False)
    session_id: str = field(init=False)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)
    current_iteration: int = 0

    def __post_init__(self):
        """初始化后设置"""
        self.enabled = self.config.enabled
        self.session_id = generate_session_id()
        logger.debug(f"ThoughtRecorder初始化，会话ID: {self.session_id}")

    def record_llm_call(
        self,
        iteration: Optional[int],
        messages: List[Dict[str, str]],
        response: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录一次LLM调用

        Args:
            iteration: 迭代号，如果为None则使用current_iteration
            messages: 输入消息列表
            response: LLM响应
            metadata: 元数据（provider, model, thinking_content等）
        """
        if not self.enabled:
            return

        try:
            thought = {
                "type": "llm_call",
                "timestamp": time.time(),
                "formatted_timestamp": format_timestamp(),
                "session_id": self.session_id,
                "iteration": iteration if iteration is not None else self.current_iteration,
                "messages": sanitize_for_logging(messages),
                "response": sanitize_for_logging(response),
                "tool_calls": response.get("tool_calls", []),
                "metadata": {
                    "provider": metadata.get("provider") if metadata else None,
                    "model": metadata.get("model") if metadata else None,
                    "thinking_supported": metadata.get("thinking_supported", False) if metadata else False,
                    "thinking_content": metadata.get("thinking_content") if metadata else None,
                    "duration_ms": metadata.get("duration_ms") if metadata else None,
                    "estimated_tokens": metadata.get("estimated_tokens") if metadata else None,
                }
            }

            # 清理元数据中的None值
            thought["metadata"] = {
                k: v for k, v in thought["metadata"].items()
                if v is not None
            }

            self.thoughts.append(thought)
            logger.debug(f"记录LLM调用，迭代: {thought['iteration']}")

        except Exception as e:
            logger.error(f"记录LLM调用失败: {e}", exc_info=True)

    def record_tool_decision(
        self,
        iteration: Optional[int],
        tool_name: str,
        input_data: Dict[str, Any],
        reasoning: Optional[str],
        result: Dict[str, Any]
    ) -> None:
        """记录工具调用决策

        Args:
            iteration: 迭代号，如果为None则使用current_iteration
            tool_name: 工具名称
            input_data: 输入参数
            reasoning: 调用理由
            result: 工具执行结果
        """
        if not self.enabled:
            return

        try:
            thought = {
                "type": "tool_decision",
                "timestamp": time.time(),
                "formatted_timestamp": format_timestamp(),
                "session_id": self.session_id,
                "iteration": iteration if iteration is not None else self.current_iteration,
                "tool_name": tool_name,
                "input": sanitize_for_logging(input_data),
                "reasoning": reasoning,
                "result": sanitize_for_logging(result),
            }

            self.thoughts.append(thought)
            logger.debug(f"记录工具调用决策: {tool_name}")

        except Exception as e:
            logger.error(f"记录工具调用决策失败: {e}", exc_info=True)

    def record_iteration_state(
        self,
        iteration: Optional[int],
        state: Dict[str, Any]
    ) -> None:
        """记录迭代状态

        Args:
            iteration: 迭代号，如果为None则使用current_iteration
            state: 状态信息
        """
        if not self.enabled:
            return

        try:
            thought = {
                "type": "iteration_state",
                "timestamp": time.time(),
                "formatted_timestamp": format_timestamp(),
                "session_id": self.session_id,
                "iteration": iteration if iteration is not None else self.current_iteration,
                "state": sanitize_for_logging(state),
            }

            self.thoughts.append(thought)
            logger.debug(f"记录迭代状态，迭代: {thought['iteration']}")

        except Exception as e:
            logger.error(f"记录迭代状态失败: {e}", exc_info=True)

    def get_thoughts_by_type(self, thought_type: str) -> List[Dict[str, Any]]:
        """按类型获取思考记录

        Args:
            thought_type: 记录类型（llm_call, tool_decision, iteration_state）

        Returns:
            该类型的所有记录
        """
        return [t for t in self.thoughts if t["type"] == thought_type]

    def get_thoughts_by_iteration(self, iteration: int) -> List[Dict[str, Any]]:
        """按迭代号获取思考记录

        Args:
            iteration: 迭代号

        Returns:
            该迭代的所有记录
        """
        return [t for t in self.thoughts if t["iteration"] == iteration]

    def clear_thoughts(self) -> None:
        """清空所有思考记录"""
        self.thoughts.clear()
        logger.debug("已清空所有思考记录")

    def update_iteration(self, iteration: int) -> None:
        """更新当前迭代号

        Args:
            iteration: 新的迭代号
        """
        self.current_iteration = iteration
        logger.debug(f"更新当前迭代号为: {iteration}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        if not self.thoughts:
            return {"total": 0}

        stats = {
            "total": len(self.thoughts),
            "by_type": {},
            "by_iteration": {},
            "session_id": self.session_id,
            "first_timestamp": min(t["timestamp"] for t in self.thoughts),
            "last_timestamp": max(t["timestamp"] for t in self.thoughts),
        }

        # 按类型统计
        for thought in self.thoughts:
            thought_type = thought["type"]
            stats["by_type"][thought_type] = stats["by_type"].get(thought_type, 0) + 1

            # 按迭代统计
            iteration = thought["iteration"]
            stats["by_iteration"][iteration] = stats["by_iteration"].get(iteration, 0) + 1

        return stats