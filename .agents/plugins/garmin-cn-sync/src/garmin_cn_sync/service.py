from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .config import database_path, import_dir
from .database import Database
from .importers import import_directory
from .secrets import SecretStore
from .sync import SyncEngine


def _nested(data: Any, *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = data
        for key in path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)
        if value is not None:
            return value
    return None


class GarminService:
    def __init__(self, database: Database | None = None, engine: SyncEngine | None = None) -> None:
        self.database = database or Database(database_path())
        self.engine = engine or SyncEngine(self.database)

    def status(self) -> dict[str, Any]:
        result = self.database.status()
        result.update({"region": "China (garmin.cn)", "read_only": True,
                       "credentials_configured": SecretStore().load_credentials() is not None,
                       "import_directory": str(import_dir())})
        return result

    def sync_now(self, health_days: int = 2, activity_days: int = 7) -> dict[str, Any]:
        return self.engine.sync(health_days=health_days, activity_days=activity_days)

    def daily(self, start_date: str, end_date: str, include_raw: bool = False) -> list[dict[str, Any]]:
        rows = self.database.daily(start_date, end_date)
        if include_raw:
            return rows
        result = []
        for row in rows:
            summary, sleep, hrv = row.get("summary") or {}, row.get("sleep") or {}, row.get("hrv") or {}
            result.append({"date": row["calendar_date"],
                "steps": _nested(summary, ("totalSteps",), ("steps",)),
                "resting_heart_rate": _nested(summary, ("restingHeartRate",), ("minHeartRate",)),
                "average_stress": _nested(summary, ("averageStressLevel",), ("avgStressLevel",)),
                "sleep_seconds": _nested(sleep, ("dailySleepDTO", "sleepTimeSeconds"), ("sleepTimeSeconds",)),
                "sleep_score": _nested(sleep, ("dailySleepDTO", "sleepScores", "overall", "value"),
                                       ("sleepScores", "overall", "value")),
                "hrv_last_night_average": _nested(hrv, ("hrvSummary", "lastNightAvg"), ("lastNightAvg",)),
                "body_battery": row.get("body_battery"), "errors": row.get("errors"),
                "synced_at": row.get("synced_at")})
        return result

    def activities(self, start_date: str, end_date: str, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        return self.database.activities(start_date, end_date, limit)

    def trends(self, days: int = 28) -> dict[str, Any]:
        if not 2 <= days <= 366:
            raise ValueError("days must be between 2 and 366")
        end = date.today()
        start = end - timedelta(days=days - 1)
        rows = self.daily(start.isoformat(), end.isoformat(), include_raw=False)
        fields = ("steps", "resting_heart_rate", "average_stress", "sleep_seconds", "sleep_score", "hrv_last_night_average")
        metrics: dict[str, Any] = {}
        midpoint = max(1, len(rows) // 2)
        for field in fields:
            values = [float(row[field]) for row in rows if isinstance(row.get(field), (int, float))]
            if not values:
                continue
            first = [float(row[field]) for row in rows[:midpoint] if isinstance(row.get(field), (int, float))]
            second = [float(row[field]) for row in rows[midpoint:] if isinstance(row.get(field), (int, float))]
            metrics[field] = {"count": len(values), "average": sum(values) / len(values),
                "first_half_average": None if not first else sum(first) / len(first),
                "second_half_average": None if not second else sum(second) / len(second)}
        return {"start_date": start.isoformat(), "end_date": end.isoformat(), "days": days, "metrics": metrics}

    def import_files(self) -> dict[str, Any]:
        return import_directory(self.database, import_dir())
