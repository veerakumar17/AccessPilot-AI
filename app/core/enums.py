from enum import Enum


class AuditStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ViolationSeverity(str, Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class DisabilityType(str, Enum):
    BLIND = "blind"
    COLOR_BLIND = "color_blind"
    LOW_VISION = "low_vision"
    KEYBOARD = "keyboard"
    COGNITIVE = "cognitive"


class FixType(str, Enum):
    HTML = "html"
    CSS = "css"
    JSX = "jsx"
    ARIA = "aria"
