from __future__ import annotations


class SPExecutionError(RuntimeError):
    """Base error for Safety repository execution failures."""

    def __init__(
        self,
        message: str,
        *,
        statement: str | None = None,
        params: object = None,
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.statement = statement
        self.params = params
        self.original_exception = original_exception


class SPTimeoutError(SPExecutionError):
    """Raised when a database operation exceeds its timeout."""


class SPDeadlockError(SPExecutionError):
    """Raised when a database deadlock persists after retries."""


class SPParameterError(SPExecutionError):
    """Raised when repository input parameters are invalid."""


class PhaseTransitionError(RuntimeError):
    """Raised when a Safety workflow phase transition is not allowed."""


class AnonymityMaskError(RuntimeError):
    """Raised when Near Miss anonymity rules would be violated."""
