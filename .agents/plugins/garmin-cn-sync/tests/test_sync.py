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
