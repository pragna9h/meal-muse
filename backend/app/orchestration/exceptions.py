class OrchestrationError(Exception):
    """Base exception for MealMuse orchestration failures."""


class ToolSelectionError(OrchestrationError):
    """Raised when MealMuse cannot select or validate a tool call."""


class ToolExecutionError(OrchestrationError):
    """Raised when an application tool fails during execution."""