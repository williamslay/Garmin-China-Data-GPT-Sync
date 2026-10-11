from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Callable

from .client import GarminClientFactory
from .database import Database


class SyncEngine:
    def __init__(self, database: Database, connect: Callable[[], Any] | None = None) -> None:
        self.database = database
        self.connect = connect or GarminClientFactory().connect

    def sync(self, health_days: int = 2, activity_days: int = 7) -> dict[str, Any]:
        if not 1 <= health_days <= 31:
            raise ValueError("health_days must be between 1 and 31")
        if not 1 <= activity_days <= 366:
            raise ValueError("activity_days must be between 1 and 366")
        run_id = self.database.start_run()
        details: dict[str, Any] = {"daily_dates": 0, "activities": 0, "errors": {}}
        try:
            session = self.connect()
            api = session.api
            end = date.today()
            health_start = end - timedelta(days=health_days - 1)
            for offset in range(health_days):
                current = (health_start + timedelta(days=offset)).isoformat()
                values: dict[str, Any] = {}
                errors: dict[str, str] = {}
                calls = {
                    "summary": lambda d=current: api.get_stats(d),
                    "sleep": lambda d=current: api.get_sleep_data(d),
                    "hrv": lambda d=current: api.get_hrv_data(d),
                    "body_battery": lambda d=current: api.get_body_battery(d, d),
                }
                for kind, call in calls.items():
                    try:
                        values[kind] = call()
                    except Exception as exc:
                        errors[kind] = self._safe_error(exc)
                self.database.upsert_daily(current, values, errors)
                details["daily_dates"] += 1
                if errors:
                    details["errors"][current] = errors
            activity_start = (end - timedelta(days=activity_days - 1)).isoformat()
            try:
                activities = api.get_activities_by_date(activity_start, end.isoformat())
                for activity in activities:
                    self.database.upsert_activity(activity)
                details["activities"] = len(activities)
            except Exception as exc:
                details["errors"]["activities"] = self._safe_error(exc)
            persist = getattr(session, "persist_tokens", None)
            if callable(persist):
                persist()
            status = "partial" if details["errors"] else "ok"
            self.database.finish_run(run_id, status, details)
            return {"status": status, **details}
        except Exception as exc:
            details["fatal_error"] = self._safe_error(exc)
            self.database.finish_run(run_id, "failed", details)
            raise

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        text = f"{type(exc).__name__}: {exc}"
        if "?" in text:
            text = text.split("?", 1)[0] + "?<redacted>"
        return text[:500]
