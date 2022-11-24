from enum import Enum


class StrEnum(str, Enum):
    def __repr__(self):
        return self.name

    def __str__(self):
        return self.value


class ResponseStatusEnum(StrEnum):
    PENDING: str = "pending"
    ASSIGNED: str = "assigned"
    COMPLETED: str = "completed"
    ERROR: str = "error"


class ErrorTitle(StrEnum):
    UNKNOWN: str = "Unknown Error"
    INPUT_VALIDATION: str = "Input Validation Error"
    TIMEOUT: str = "TimeOut Error"
    WRONG_TASK_ID: str = "Wrong Task ID Error"


class ErrorMessage(StrEnum):
    UNKNOWN: str = "Unknown error occurred.\nPlease share the error with our community manager.\n"


class WarningMessages(StrEnum):
    NSFW: str = "Potential NSFW content was detected in one or more images.\nIf you want to see the original image, press the button below."
