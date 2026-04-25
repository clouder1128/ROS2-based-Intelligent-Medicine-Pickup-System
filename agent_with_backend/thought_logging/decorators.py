# agent_with_backend/P1/thought_logging/decorators.py
import functools
import logging
from typing import Callable, Any, Optional
from inspect import signature

from .config import ThoughtLoggingConfig
from .recorder import ThoughtRecorder
from .output import OutputManager

logger = logging.getLogger(__name__)

def record_llm_calls(recorder: ThoughtRecorder):
    """装饰器：记录LLM调用

    Args:
        recorder: ThoughtRecorder实例

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        """实际装饰器"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """包装函数"""

            # 执行前：准备记录数据
            iteration = kwargs.get('iteration')
            metadata = {k: v for k, v in kwargs.items() if k != 'iteration'}

            try:
                # 执行原始函数
                result = func(*args, **kwargs)

                # 执行后：记录LLM调用
                if recorder.enabled:
                    try:
                        # 提取消息和响应
                        # 假设第一个位置参数是messages，或者有关键字参数messages
                        messages = None
                        if args and isinstance(args[0], list):
                            messages = args[0]
                        elif 'messages' in kwargs:
                            messages = kwargs['messages']

                        if messages is not None:
                            recorder.record_llm_call(
                                iteration=iteration,
                                messages=messages,
                                response=result,
                                metadata=metadata
                            )
                    except Exception as e:
                        logger.error(f"记录LLM调用失败: {e}", exc_info=True)
                        # 不重新抛出异常，避免影响主流程

                return result

            except Exception as e:
                # 记录错误
                if recorder.enabled:
                    try:
                        error_metadata = {k: v for k, v in kwargs.items() if k != 'iteration'}
                        error_metadata['error'] = str(e)
                        recorder.record_llm_call(
                            iteration=iteration,
                            messages=[],
                            response={"error": str(e)},
                            metadata=error_metadata
                        )
                    except Exception as record_error:
                        logger.error(f"记录错误失败: {record_error}", exc_info=True)

                # 重新抛出原始异常
                raise

        return wrapper

    return decorator

def record_tool_decisions(recorder: ThoughtRecorder):
    """装饰器：记录工具调用决策

    Args:
        recorder: ThoughtRecorder实例

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        """实际装饰器"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """包装函数"""

            # 提取参数
            tool_name = None
            tool_input = None
            reasoning = kwargs.get('reasoning')
            iteration = kwargs.get('iteration')

            # 根据参数位置或名称提取
            if args:
                if len(args) >= 1:
                    tool_name = args[0]
                if len(args) >= 2:
                    tool_input = args[1]
            else:
                tool_name = kwargs.get('tool_name')
                tool_input = kwargs.get('tool_input')

            try:
                # 执行原始函数
                result = func(*args, **kwargs)

                # 执行后：记录工具调用决策
                if recorder.enabled and tool_name is not None:
                    try:
                        recorder.record_tool_decision(
                            iteration=iteration,
                            tool_name=tool_name,
                            input_data=tool_input or {},
                            reasoning=reasoning,
                            result=result
                        )
                    except Exception as e:
                        logger.error(f"记录工具调用决策失败: {e}", exc_info=True)
                        # 不重新抛出异常，避免影响主流程

                return result

            except Exception as e:
                # 记录错误
                if recorder.enabled and tool_name is not None:
                    try:
                        recorder.record_tool_decision(
                            iteration=iteration,
                            tool_name=tool_name,
                            input_data=tool_input or {},
                            reasoning=reasoning,
                            result={"error": str(e)}
                        )
                    except Exception as record_error:
                        logger.error(f"记录工具错误失败: {record_error}", exc_info=True)

                # 重新抛出原始异常
                raise

        return wrapper

    return decorator

class ThoughtLoggingDecorator:
    """思考记录装饰器类"""

    def __init__(self, config: ThoughtLoggingConfig):
        self.config = config
        self.recorder = ThoughtRecorder(config)
        self.output_manager = OutputManager(config)

        # 连接recorder和output_manager
        self._connect_recorder_to_output()

        logger.debug(f"ThoughtLoggingDecorator初始化")

    def _connect_recorder_to_output(self):
        """连接recorder到output_manager"""
        # 创建一个包装recorder的方法，在记录时同时输出
        original_record_methods = {
            'record_llm_call': self.recorder.record_llm_call,
            'record_tool_decision': self.recorder.record_tool_decision,
            'record_iteration_state': self.recorder.record_iteration_state,
        }

        def make_wrapped_method(method_name, original_method):
            def wrapped_method(*args, **kwargs):
                # 调用原始方法
                result = original_method(*args, **kwargs)

                # 获取最新记录并输出
                if self.recorder.thoughts:
                    latest_thought = self.recorder.thoughts[-1]
                    self.output_manager.write_thought(latest_thought)

                return result

            return wrapped_method

        # 替换recorder的方法
        for method_name, original_method in original_record_methods.items():
            wrapped_method = make_wrapped_method(method_name, original_method)
            setattr(self.recorder, method_name, wrapped_method)

    def decorate_class(self, cls):
        """装饰一个类，为其添加思考记录功能

        Args:
            cls: 要装饰的类

        Returns:
            装饰后的类
        """
        # 保存原始__init__
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            # 调用原始__init__
            original_init(self, *args, **kwargs)

            # 添加recorder属性
            self._recorder = self.recorder

            # 装饰特定方法
            self._decorate_methods()

        # 替换__init__
        cls.__init__ = new_init

        # 添加装饰器属性
        cls.recorder = self.recorder
        cls.output_manager = self.output_manager
        cls._decorate_methods = lambda self: self._decorate_instance_methods()

        # 为实例添加方法装饰逻辑
        def _decorate_instance_methods(self):
            """装饰实例方法"""
            # 这里可以根据需要装饰特定方法
            # 例如：如果类有chat方法，用record_llm_calls装饰
            if hasattr(self, 'chat'):
                self.chat = record_llm_calls(self._recorder)(self.chat)

            # 如果类有run方法，记录迭代状态
            if hasattr(self, 'run'):
                original_run = self.run

                @functools.wraps(original_run)
                def wrapped_run(*args, **kwargs):
                    # 记录迭代开始
                    if self._recorder.enabled:
                        self._recorder.record_iteration_state(
                            iteration=self._recorder.current_iteration,
                            state={"method": "run", "args": args, "kwargs": kwargs}
                        )

                    # 执行原始方法
                    result = original_run(*args, **kwargs)

                    # 更新迭代计数器
                    if self._recorder.enabled:
                        self._recorder.update_iteration(self._recorder.current_iteration + 1)

                    return result

                self.run = wrapped_run

        cls._decorate_instance_methods = _decorate_instance_methods

        return cls

def with_thought_logging(obj, config: Optional[ThoughtLoggingConfig] = None):
    """为对象添加思考记录功能

    Args:
        obj: 要装饰的对象（类或实例）
        config: 配置对象，如果为None则使用默认配置

    Returns:
        装饰后的对象
    """
    if config is None:
        config = ThoughtLoggingConfig()

    decorator = ThoughtLoggingDecorator(config)

    if isinstance(obj, type):
        # 装饰类
        return decorator.decorate_class(obj)
    else:
        # 装饰实例
        # 添加recorder属性
        obj._recorder = decorator.recorder
        obj._output_manager = decorator.output_manager

        # 装饰实例方法
        if hasattr(obj, 'chat'):
            obj.chat = record_llm_calls(obj._recorder)(obj.chat)

        if hasattr(obj, 'run'):
            original_run = obj.run

            @functools.wraps(original_run)
            def wrapped_run(*args, **kwargs):
                # 记录迭代开始
                if obj._recorder.enabled:
                    obj._recorder.record_iteration_state(
                        iteration=obj._recorder.current_iteration,
                        state={"method": "run", "args": args, "kwargs": kwargs}
                    )

                # 执行原始方法
                result = original_run(*args, **kwargs)

                # 更新迭代计数器
                if obj._recorder.enabled:
                    obj._recorder.update_iteration(obj._recorder.current_iteration + 1)

                return result

            obj.run = wrapped_run

        # 如果对象有llm_client属性，并且llm_client有chat方法，也装饰它
        if hasattr(obj, 'llm_client'):
            llm_client = obj.llm_client
            if hasattr(llm_client, 'chat'):
                llm_client.chat = record_llm_calls(obj._recorder)(llm_client.chat)

        return obj