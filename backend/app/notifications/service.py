"""
DataGuard Notification Service
Dispatches and stores alerts for high/critical anomalies and pipeline failures.
"""

from typing import Any
from datetime import datetime
from uuid import uuid4


class NotificationService:
    """
    Manages operational notifications and dashboard alerts.
    """

    _alerts: list[dict[str, Any]] = []

    @classmethod
    def emit_inspection_alerts(
        cls,
        inspection_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Scans findings and triggers alerts for CRITICAL and HIGH severity issues.
        """
        findings = inspection_data.get("inspection", {}).get("findings", [])
        dataset = inspection_data.get("dataset_path", "Dataset Stream")
        new_alerts = []

        for f in findings:
            sev = f.get("severity", "LOW")
            if sev in ["CRITICAL", "HIGH"]:
                alert = {
                    "id": str(uuid4()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": sev,
                    "dataset": dataset,
                    "finding_type": f.get("type"),
                    "title": f"[{sev}] {f.get('type')} in {dataset}",
                    "message": f.get("message"),
                    "is_read": False,
                }
                cls._alerts.insert(0, alert)
                new_alerts.append(alert)

        # Cap stored alerts to 100
        cls._alerts = cls._alerts[:100]
        return new_alerts

    @classmethod
    def get_alerts(cls, unread_only: bool = False) -> list[dict[str, Any]]:
        if unread_only:
            return [a for a in cls._alerts if not a["is_read"]]
        return cls._alerts

    @classmethod
    def mark_all_read(cls) -> None:
        for a in cls._alerts:
            a["is_read"] = True
