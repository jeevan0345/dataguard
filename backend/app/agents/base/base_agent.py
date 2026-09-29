"""
DataGuard Base Agent
Defines the standard interface and execution lifecycle for all DataGuard agents.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import time
from typing import Any


class BaseAgent(ABC):
    """
    Abstract Base Class for all autonomous DataGuard agents.
    Enforces standardized execution, telemetry, and structured outputs.
    """

    def __init__(
        self,
        name: str,
        role: str,
        description: str,
    ) -> None:
        self.name = name
        self.role = role
        self.description = description
        self.last_run_at: datetime | None = None
        self.last_duration_ms: float = 0.0

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Core agent execution logic. Must be implemented by subclasses.
        """
        pass

    def execute(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Wraps agent run with execution telemetry and standard metadata.
        """
        start_time = time.perf_counter()
        self.last_run_at = datetime.utcnow()

        try:
            result = self.run(*args, **kwargs)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.last_duration_ms = duration_ms

            if isinstance(result, dict):
                result["agent_metadata"] = {
                    "name": self.name,
                    "role": self.role,
                    "executed_at": self.last_run_at.isoformat(),
                    "duration_ms": duration_ms,
                    "status": "COMPLETED",
                }
            return result

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.last_duration_ms = duration_ms
            return {
                "agent_metadata": {
                    "name": self.name,
                    "role": self.role,
                    "executed_at": self.last_run_at.isoformat(),
                    "duration_ms": duration_ms,
                    "status": "FAILED",
                    "error": str(exc),
                },
                "status": "FAILED",
                "error": str(exc),
                "findings": [],
            }
