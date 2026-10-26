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
        session = None
        try:
            session = self.connect()
            api = session.api
            provider = getattr(session, "provider", "china-web")
            details["provider"] = provider
            end = date.today()
            health_start = end - timedelta(days=health_days - 1)
            batch = getattr(api, "get_daily_batch", None)
            batch_values, batch_errors = (batch(health_start.isoformat(), end.isoformat())
                if callable(batch) else ({}, {}))
            for offset in range(health_days):
                current = (health_start + timedelta(days=offset)).isoformat()
                values: dict[str, Any] = {}
                errors: dict[str, str] = {}
                calls = {} if callable(batch) else {
                    "summary": lambda d=current: api.get_stats(d),
                    "sleep": lambda d=current: api.get_sleep_data(d),
                    "hrv": lambda d=current: api.get_hrv_data(d),
                    "body_battery": lambda d=current: api.get_body_battery(d, d),
                }
                if callable(batch):
                    values = batch_values[current]
                    errors = batch_errors[current]
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
                    self.database.upsert_activity(activity,
                        source="garmin-cn-personal-api" if provider == "personal-api" else "garmin-cn")
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
        finally:
            close = getattr(session, "close", None)
            if callable(close):
                close()

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        text = f"{type(exc).__name__}: {exc}"
        if "?" in text:
            text = text.split("?", 1)[0] + "?<redacted>"
        return text[:500]
