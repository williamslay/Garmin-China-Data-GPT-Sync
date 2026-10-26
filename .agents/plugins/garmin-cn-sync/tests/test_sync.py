from pathlib import Path

from garmin_cn_sync.database import Database
from garmin_cn_sync.sync import SyncEngine


class FakeApi:
    def get_stats(self, day): return {"calendarDate": day, "totalSteps": 1000}
    def get_sleep_data(self, day): return {"calendarDate": day, "sleepTimeSeconds": 28800}
    def get_hrv_data(self, day): return {"calendarDate": day, "lastNightAvg": 45}
    def get_body_battery(self, start, end): return [{"date": start, "charged": 50}]
    def get_activities_by_date(self, start, end):
        return [{"activityId": 7, "activityName": "Run", "activityType": {"typeKey": "running"},
                 "startTimeLocal": f"{end} 08:00:00"}]


class FakeSession:
    def __init__(self):
        self.api = FakeApi()
        self.persisted = False

    def persist_tokens(self): self.persisted = True


def test_sync_writes_daily_and_activities(tmp_path: Path) -> None:
    db = Database(tmp_path / "sync.sqlite3")
    session = FakeSession()
    result = SyncEngine(db, connect=lambda: session).sync(health_days=2, activity_days=7)
    assert result["status"] == "ok"
    assert result["daily_dates"] == 2
    assert result["activities"] == 1
    assert db.status()["daily_records"] == 2
    assert db.status()["activity_records"] == 1
    assert session.persisted is True


def test_official_batch_sync_marks_source_and_closes_session(tmp_path: Path):
    class BatchApi:
        def get_daily_batch(self, start, end):
            return {end: {"sleep": {"sleepTimeSeconds": 28800}}}, {end: {}}
        def get_activities_by_date(self, start, end):
            return [{"activityId": 11, "startTimeLocal": end + " 12:00:00"}]
    class BatchSession:
        provider = "personal-api"
        api = BatchApi()
        closed = False
        def persist_tokens(self): pass
        def close(self): self.closed = True
    db = Database(tmp_path / "sync.sqlite3")
    session = BatchSession()
    result = SyncEngine(db, connect=lambda: session).sync(health_days=1)
    assert result["provider"] == "personal-api"
    assert result["status"] == "ok"
    assert session.closed
    from datetime import date
    day = date.today().isoformat()
    assert db.activities(day, day, 1)[0]["source"] == "garmin-cn-personal-api"
