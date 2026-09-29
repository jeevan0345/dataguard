from enum import Enum


class PipelineStatus(str, Enum):
    CREATED = "Created"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILED = "Failed"
    PAUSED = "Paused"