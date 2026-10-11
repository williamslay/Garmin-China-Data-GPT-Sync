from pathlib import Path

from garmin_cn_sync.database import Database


def test_daily_upsert_preserves_existing_values(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.sqlite3")
    db.upsert_daily("2026-09-14", {"summary": {"totalSteps": 1234}}, {})
    db.upsert_daily("2026-09-14", {"sleep": {"sleepTimeSeconds": 3600}}, {"hrv": "missing"})
    row = db.daily("2026-09-14", "2026-09-14")[0]
    assert row["summary"]["totalSteps"] == 1234
    assert row["sleep"]["sleepTimeSeconds"] == 3600
    assert row["errors"] == {"hrv": "missing"}


def test_activity_upsert_and_query(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.sqlite3")
    db.upsert_activity({"activityId": 42, "activityName": "Morning Run",
                        "activityType": {"typeKey": "running"},
                        "startTimeLocal": "2026-09-14 07:00:00"})
    rows = db.activities("2026-09-01", "2026-09-30", 10)
    assert rows[0]["activity_id"] == "42"
    assert rows[0]["activity_type"] == "running"
