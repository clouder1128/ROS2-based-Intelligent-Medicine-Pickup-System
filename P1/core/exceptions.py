# exceptions.py
class AgentError(Exception):
    """Base exception for Agent related errors."""
    def __init__(self, message: str = "Agent error occurred") -> None:
        super().__init__(message)

class LLMError(AgentError):
    """Raised when LLM API call fails."""
    def __init__(self, message: str = "LLM error occurred") -> None:
        super().__init__(message)

class ToolExecutionError(AgentError):
    """Raised when a tool execution fails."""
    def __init__(self, message: str = "Tool execution error") -> None:
        super().__init__(message)

class ValidationError(AgentError):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message)

class ApprovalRequiredError(AgentError):
    """Raised when approval is required but not yet given."""
    def __init__(self, message: str = "Approval required") -> None:
        super().__init__(message)

class ConfigurationError(AgentError):
    """Raised when configuration is invalid."""
    def __init__(self, message: str = "Configuration error") -> None:
        super().__init__(message)

class SessionError(AgentError):
    """Raised when session save/load fails."""
    def __init__(self, message: str = "Session error") -> None:
        super().__init__(message)


class WorkflowError(AgentError):
    """Raised when workflow execution fails."""
    def __init__(self, message: str = "Workflow error", workflow_id: str = None, step: str = None) -> None:
        self.workflow_id = workflow_id
        self.step = step
        full_message = message
        if workflow_id:
            full_message += f" (workflow: {workflow_id})"
        if step:
            full_message += f" (step: {step})"
        super().__init__(full_message)


class AsyncError(AgentError):
    """Raised when async operation fails."""
    def __init__(self, message: str = "Async operation error", task_id: str = None) -> None:
        self.task_id = task_id
        full_message = message
        if task_id:
            full_message += f" (task: {task_id})"
        super().__init__(full_message)