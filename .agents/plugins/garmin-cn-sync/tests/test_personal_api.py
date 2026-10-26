import base64
import json

import pytest

from garmin_cn_sync.personal_api import PersonalApiClient, PersonalApiError
from garmin_cn_sync.database import Database
from garmin_cn_sync.service import GarminService
from garmin_cn_sync.config import selected_provider
from garmin_cn_sync.client import GarminClientFactory
from garmin_cn_sync.secrets import SecretStore


def jwt(exp=10000):
    return "header." + base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode().rstrip("=") + ".signature"


class Store:
    key = "test-personal-key"
    tokens = None
    def load_personal_api_key(self): return self.key
    def load_personal_tokens(self): return self.tokens
    def save_personal_tokens(self, value): self.tokens = value


class Response:
    def __init__(self, payload=None, status=200, text=""):
        self.payload, self.status_code, self.text = payload, status, text
    def json(self): return self.payload


class Http:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.closed = False
    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        assert url.startswith("https://personal.connectapi.garmin.cn/")
        assert kwargs["allow_redirects"] is False
        return self.responses.pop(0)
    def close(self): self.closed = True


def client(responses, store=None):
    http = Http(responses)
    return PersonalApiClient(store or Store(), http, clock=lambda: 0), http


def test_vault_token_reuse_expiry_and_key_rotation():
    store = Store()
    first, http = client([Response(text=jwt())], store)
    first.authenticate()
    assert len(http.calls) == 1
    second, http2 = client([], store)
    second.authenticate()
    assert not http2.calls
    second.clock = lambda: 9000  # Within the one-hour refresh window.
    http2.responses.append(Response(text=jwt(20000)))
    second.authenticate()
    assert len(http2.calls) == 1
    store.key = "rotated-personal-key"
    http2.responses.append(Response(text=jwt(30000)))
    second.authenticate()
    assert len(http2.calls) == 2


def test_401_refreshes_once_and_other_failures_do_not_retry():
    api, http = client([Response(text=jwt()), Response(status=401), Response(text=jwt()), Response({"ok": True})])
    assert api.get("/test") == {"ok": True}
    assert [x[0] for x in http.calls] == ["POST", "GET", "POST", "GET"]
    api, http = client([Response(text=jwt()), Response(status=429, text="secret-response")])
    with pytest.raises(PersonalApiError, match="HTTP 429") as error:
        api.get("/test")
    assert "secret-response" not in str(error.value)
    assert len(http.calls) == 2


def test_failed_token_exchange_has_safe_error():
    api, _ = client([Response(status=526, text="never-log-this-body")])
    with pytest.raises(PersonalApiError, match="HTTP 526") as error:
        api.authenticate()
    assert "never-log" not in str(error.value)


def test_provider_selection_and_official_failure_never_uses_web(monkeypatch):
    monkeypatch.delenv("GARMIN_CN_SYNC_PROVIDER", raising=False)
    assert selected_provider(True) == "personal-api"
    assert selected_provider(False) == "china-web"
    monkeypatch.setenv("GARMIN_CN_SYNC_PROVIDER", "web")
    assert selected_provider(True) == "china-web"
    monkeypatch.setenv("GARMIN_CN_SYNC_PROVIDER", "personal")
    assert selected_provider(False) == "personal-api"
    def fail_auth(self, force=False):
        raise PersonalApiError("HTTP 526")
    monkeypatch.setattr(PersonalApiClient, "authenticate", fail_auth)
    # This store has no web-credential methods: any accidental fallback fails the test.
    with pytest.raises(PersonalApiError, match="526"):
        GarminClientFactory(secrets=Store()).connect()


def test_bearer_chunks_and_web_credentials_stay_isolated(monkeypatch):
    class Vault:
        data = {}
        def get_password(self, service, name): return self.data.get((service, name))
        def set_password(self, service, name, value): self.data[service, name] = value
        def delete_password(self, service, name): del self.data[service, name]
    vault = Vault()
    monkeypatch.setattr(SecretStore, "_keyring", staticmethod(lambda: vault))
    store = SecretStore("test-store")
    store.save_credentials("user@example.invalid", "fake-password")
    store.save_tokens('{"web_token":"original"}')
    store.save_personal_api_key("synthetic-personal-api-key")
    large_token = json.dumps({"access_token": "x" * 5000})
    store.save_personal_tokens(large_token)
    assert store.load_personal_tokens() == large_token
    assert store.load_tokens() == '{"web_token":"original"}'
    assert store.load_credentials().password == "fake-password"
    assert max(len(v) for (service, name), v in vault.data.items()) <= 900


def test_batched_health_preserves_existing_query_contract_and_reports_gaps(tmp_path):
    day, missing = "2026-10-24", "2026-10-25"
    summary = {"calendarDate": day, "movement": {"steps": {"value": 5432}},
               "heartRate": {"restingValue": 51}, "stress": {"avgLevel": 20}}
    sleep = {"calendarDate": day, "sleepTimeSeconds": 28800, "sleepScores": {"overall": {"value": 90}}}
    hrv = {"calendarDate": day, "lastNightAvg": 47}
    api, http = client([Response(text=jwt()), Response({"data": [summary]}), Response([sleep]),
                       Response({"hrvSummaries": [hrv]}), Response([{"date": day, "charged": 60}])])
    values, errors = api.get_daily_batch(day, missing)
    assert len(http.calls) == 5  # Four range calls plus one authentication.
    db = Database(tmp_path / "test.sqlite3")
    db.upsert_daily(missing, {"sleep": {"sleepTimeSeconds": 27000}}, {})
    for date in (day, missing):
        db.upsert_daily(date, values[date], errors[date])
    rows = GarminService(database=db).daily(day, missing)
    assert [rows[0][k] for k in ("steps", "resting_heart_rate", "average_stress", "sleep_seconds", "sleep_score", "hrv_last_night_average")] == [5432, 51, 20, 28800, 90, 47]
    assert rows[1]["sleep_seconds"] == 27000  # Missing batch data must not erase a prior result.
    assert len(rows[1]["errors"]) == 4


def test_bad_batch_does_not_silently_commit_partial_category():
    day = "2026-10-24"
    api, _ = client([Response(text=jwt()), Response({"data": [{"calendarDate": day}, {"calendarDate": day}]}),
                     Response([]), Response({"wrongWrapper": []}), Response([])])
    values, errors = api.get_daily_batch(day, day)
    assert values[day] == {}
    assert len(errors[day]) == 4


def test_activity_pagination_fetches_second_page_and_detects_repeated_page():
    page = [{"activityId": n + 1} for n in range(100)]
    api, http = client([Response(text=jwt()), Response(page), Response([{"activityId": 101}])])
    assert len(api.get_activities_by_date("2026-01-01", "2026-10-25")) == 101
    assert http.calls[-1][2]["params"]["start"] == 100
    api, _ = client([Response(text=jwt()), Response(page), Response(page)])
    with pytest.raises(PersonalApiError, match="repeated"):
        api.get_activities_by_date("2026-01-01", "2026-10-25")


def test_official_activity_keeps_same_activity_legacy_vo2_with_provenance(tmp_path):
    db = Database(tmp_path / "test.sqlite3")
    db.upsert_activity({"activityId": 1, "vO2MaxValue": 39, "startTimeLocal": "2026-10-25 10:00:00"})
    official = {"activityId": 1, "distance": 5000, "startTimeLocal": "2026-10-25 10:00:00"}
    db.upsert_activity(official, source="garmin-cn-personal-api")
    db.upsert_activity(official, source="garmin-cn-personal-api")
    db.upsert_activity({**official, "activityId": 2}, source="garmin-cn-personal-api")
    rows = {r["activity_id"]: r for r in db.activities("2026-10-25", "2026-10-25", 10)}
    assert rows["1"]["data"]["vO2MaxValue"] == 39
    assert rows["1"]["data"]["_retained_field_sources"] == {"vO2MaxValue": "garmin-cn"}
    assert "vO2MaxValue" not in rows["2"]["data"]
    assert "vO2MaxValue" not in official
