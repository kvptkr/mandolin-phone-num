from enum import Enum


class CallStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    FAILED = "failed"


