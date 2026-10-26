from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA busy_timeout = 30000")
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def initialize(self) -> None:
        with self.connect() as con:
            con.execute("PRAGMA journal_mode = WAL")
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS daily_snapshots (
                    calendar_date TEXT PRIMARY KEY,
                    summary_json TEXT,
                    sleep_json TEXT,
                    hrv_json TEXT,
                    body_battery_json TEXT,
                    errors_json TEXT NOT NULL DEFAULT '{}',
                    synced_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS activities (
                    activity_id TEXT PRIMARY KEY,
                    start_time TEXT,
                    activity_type TEXT,
                    name TEXT,
                    source TEXT NOT NULL DEFAULT 'garmin-cn',
                    raw_json TEXT NOT NULL,
                    synced_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_activities_start_time ON activities(start_time DESC);
                CREATE TABLE IF NOT EXISTS sync_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    details_json TEXT NOT NULL DEFAULT '{}'
                );
                """
            )

    @staticmethod
    def _dump(value: Any) -> str | None:
        return None if value is None else json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)

    @staticmethod
    def _loads(value: str | None) -> Any:
        return None if value is None else json.loads(value)

    def upsert_daily(self, calendar_date: str, values: dict[str, Any], errors: dict[str, str]) -> None:
        payloads = {name: self._dump(values.get(name)) for name in ("summary", "sleep", "hrv", "body_battery")}
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO daily_snapshots(calendar_date, summary_json, sleep_json, hrv_json,
                    body_battery_json, errors_json, synced_at) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(calendar_date) DO UPDATE SET
                    summary_json=COALESCE(excluded.summary_json,daily_snapshots.summary_json),
                    sleep_json=COALESCE(excluded.sleep_json,daily_snapshots.sleep_json),
                    hrv_json=COALESCE(excluded.hrv_json,daily_snapshots.hrv_json),
                    body_battery_json=COALESCE(excluded.body_battery_json,daily_snapshots.body_battery_json),
                    errors_json=excluded.errors_json, synced_at=excluded.synced_at
                """,
                (calendar_date, payloads["summary"], payloads["sleep"], payloads["hrv"],
                 payloads["body_battery"], self._dump(errors) or "{}", utc_now()),
            )

    def upsert_activity(self, activity: dict[str, Any], source: str = "garmin-cn") -> str:
        activity_id = str(activity.get("activityId") or activity.get("id") or "").strip()
        if not activity_id:
            raise ValueError("Activity has no activityId")
        activity_type = activity.get("activityType") or {}
        if isinstance(activity_type, dict):
            activity_type = activity_type.get("typeKey") or activity_type.get("typeId")
        start_time = activity.get("startTimeLocal") or activity.get("startTimeGMT") or activity.get("start_time")
        name = activity.get("activityName") or activity.get("name")
        with self.connect() as con:
            if source == "garmin-cn-personal-api" and activity.get("vO2MaxValue") is None:
                previous = con.execute("SELECT source,raw_json FROM activities WHERE activity_id=?",
                                       (activity_id,)).fetchone()
                if previous:
                    old = self._loads(previous["raw_json"])
                    if old.get("vO2MaxValue") is not None:
                        activity = dict(activity)
                        activity["vO2MaxValue"] = old["vO2MaxValue"]
                        activity["_retained_field_sources"] = {"vO2MaxValue":
                            old.get("_retained_field_sources", {}).get("vO2MaxValue", previous["source"])}
            con.execute(
                """
                INSERT INTO activities(activity_id,start_time,activity_type,name,source,raw_json,synced_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(activity_id) DO UPDATE SET start_time=excluded.start_time,
                    activity_type=excluded.activity_type,name=excluded.name,source=excluded.source,
                    raw_json=excluded.raw_json,synced_at=excluded.synced_at
                """,
                (activity_id, start_time, str(activity_type or ""), name, source, self._dump(activity), utc_now()),
            )
        return activity_id

    def daily(self, start: str, end: str) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT * FROM daily_snapshots WHERE calendar_date BETWEEN ? AND ? ORDER BY calendar_date",
                (start, end),
            ).fetchall()
        return [{
            "calendar_date": row["calendar_date"], "summary": self._loads(row["summary_json"]),
            "sleep": self._loads(row["sleep_json"]), "hrv": self._loads(row["hrv_json"]),
            "body_battery": self._loads(row["body_battery_json"]), "errors": self._loads(row["errors_json"]),
            "synced_at": row["synced_at"],
        } for row in rows]

    def activities(self, start: str, end: str, limit: int) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT * FROM activities WHERE substr(start_time,1,10) BETWEEN ? AND ? ORDER BY start_time DESC LIMIT ?",
                (start, end, limit),
            ).fetchall()
        return [{
            "activity_id": row["activity_id"], "start_time": row["start_time"],
            "activity_type": row["activity_type"], "name": row["name"], "source": row["source"],
            "data": self._loads(row["raw_json"]), "synced_at": row["synced_at"],
        } for row in rows]

    def start_run(self) -> int:
        with self.connect() as con:
            cur = con.execute("INSERT INTO sync_runs(started_at,status) VALUES (?,'running')", (utc_now(),))
            return int(cur.lastrowid)

    def finish_run(self, run_id: int, status: str, details: dict[str, Any]) -> None:
        with self.connect() as con:
            con.execute("UPDATE sync_runs SET finished_at=?,status=?,details_json=? WHERE id=?",
                        (utc_now(), status, self._dump(details), run_id))

    def status(self) -> dict[str, Any]:
        with self.connect() as con:
            daily_count = con.execute("SELECT COUNT(*) FROM daily_snapshots").fetchone()[0]
            activity_count = con.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
            last = con.execute("SELECT * FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()
        return {"database": str(self.path), "daily_records": daily_count, "activity_records": activity_count,
                "last_sync": None if last is None else {"started_at": last["started_at"],
                "finished_at": last["finished_at"], "status": last["status"],
                "details": self._loads(last["details_json"])}}
