from pathlib import Path

from garmin_cn_sync.database import Database
from garmin_cn_sync.service import GarminService


def test_daily_projection_and_trend(tmp_path: Path) -> None:
    db = Database(tmp_path / "db.sqlite3")
    for day, steps in (("2026-09-13", 1000), ("2026-09-14", 2000)):
        db.upsert_daily(day, {"summary": {"totalSteps": steps, "restingHeartRate": 50},
                              "sleep": {"dailySleepDTO": {"sleepTimeSeconds": 28800}},
                              "hrv": {"hrvSummary": {"lastNightAvg": 45}}}, {})
    service = GarminService(database=db)
    rows = service.daily("2026-09-13", "2026-09-14")
    assert rows[0]["steps"] == 1000
    assert rows[0]["sleep_seconds"] == 28800
