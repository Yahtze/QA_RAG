class IngestionError(Exception):
    """Base ingestion failure."""


class RetryableIngestionError(IngestionError):
    """Transient infrastructure failure; safe to retry."""

    def __init__(self, phase: str, cause: BaseException):
        super().__init__(str(cause))
        self.phase = phase
        self.cause = cause


class DeterministicIngestionError(IngestionError):
    """Content or validation failure; retry will not help."""

    def __init__(self, message: str, phase: str):
        super().__init__(message)
        self.message = message
        self.phase = phase
