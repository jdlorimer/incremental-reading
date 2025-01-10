from enum import Enum


class ErrorLevel(Enum):
    WARNING = 1
    CRITICAL = 2


class ImporterError(Exception):
    def __init__(self, level: ErrorLevel, message: str) -> None:
        super().__init__(message)

        self.errorLevel = level
        self.message = message
