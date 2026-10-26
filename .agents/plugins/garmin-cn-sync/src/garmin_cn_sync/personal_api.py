"""Read-only Garmin China Personal API adapter with OS-vault token caching."""
from __future__ import annotations

import base64
import hashlib
import json
import time
from datetime import date, timedelta
from typing import Any

import requests

from .secrets import SecretStore


class PersonalApiError(RuntimeError):
    """A safe-to-display error: never includes a response body or credential."""


class PersonalApiClient:
    BASE_URL = "https://personal.connectapi.garmin.cn"
    TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"

    def __init__(self, secrets: SecretStore, session: Any = None, clock=time.time) -> None:
        self.secrets = secrets
        self.session = session if session is not None else requests.Session()
        self.clock = clock
        self.token = ""
        self.expires_at = 0.0
        self.fingerprint = ""

    def close(self) -> None:
        self.session.close()

    def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            return self.session.request(method, self.BASE_URL + path,
                                        timeout=(10, 30), allow_redirects=False, **kwargs)
        except requests.RequestException as exc:
            raise PersonalApiError(f"Personal API {method} failed ({type(exc).__name__})") from None

    def authenticate(self, force: bool = False) -> None:
        key = self.secrets.load_personal_api_key()
        if not key:
            raise PersonalApiError("Personal API key missing. Run scripts/authenticate-personal.ps1.")
        fingerprint = hashlib.sha256((self.BASE_URL + "\0" + key).encode()).hexdigest()
        if not force:
            if self.token and self.fingerprint == fingerprint and self.expires_at > self.clock() + 3600:
                return
            cached_json = self.secrets.load_personal_tokens()
            try:
                cached = json.loads(cached_json) if cached_json else {}
                if (cached.get("fingerprint") == fingerprint
                        and float(cached.get("expires_at", 0)) > self.clock() + 3600
                        and isinstance(cached.get("access_token"), str) and cached["access_token"]):
                    self.token = cached["access_token"]
                    self.expires_at = float(cached["expires_at"])
                    self.fingerprint = fingerprint
                    return
            except (ValueError, TypeError, KeyError):
                pass
        response = self._request("POST", self.TOKEN_PATH,
                                 headers={"Authorization": "ApiKey " + key, "Accept": "*/*"})
        if response.status_code != 200:
            raise PersonalApiError(f"Personal API token exchange returned HTTP {response.status_code}")
        token = response.text.strip()
        try:
            payload = token.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            expires_at = float(claims["exp"])
            if expires_at <= self.clock():
                raise ValueError("expired")
        except (ValueError, IndexError, KeyError, TypeError):
            raise PersonalApiError("Personal API returned an invalid or expired bearer token") from None
        self.secrets.save_personal_tokens(json.dumps({"fingerprint": fingerprint,
            "access_token": token, "expires_at": expires_at}))
        self.token, self.expires_at = token, expires_at
        self.fingerprint = fingerprint

    def get(self, path: str, params: dict | None = None) -> Any:
        self.authenticate()
        response = self._request("GET", path, params=params,
            headers={"Authorization": "Bearer " + self.token, "Accept": "application/json"})
        if response.status_code == 401:
            self.authenticate(force=True)
            response = self._request("GET", path, params=params,
                headers={"Authorization": "Bearer " + self.token, "Accept": "application/json"})
        if response.status_code != 200:
            raise PersonalApiError(f"Personal API GET {path.split('?')[0]} returned HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError:
            raise PersonalApiError("Personal API returned invalid JSON") from None

    @staticmethod
    def _records(payload: Any, wrapper: str | None) -> list[dict]:
        rows = payload.get(wrapper) if wrapper and isinstance(payload, dict) else payload
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise PersonalApiError("Personal API returned an unexpected daily response shape")
        return rows

    @staticmethod
    def _summary(row: dict) -> dict:
        # Preserve the official v2 response while adding aliases understood by older MCP processes.
        result = dict(row)
        result["totalSteps"] = row.get("movement", {}).get("steps", {}).get("value")
        result["restingHeartRate"] = row.get("heartRate", {}).get("restingValue")
        result["minHeartRate"] = row.get("heartRate", {}).get("minValue")
        result["averageStressLevel"] = row.get("stress", {}).get("avgLevel")
        return result

    def get_daily_batch(self, start: str, end: str) -> tuple[dict, dict]:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        days = [(first + timedelta(days=n)).isoformat() for n in range((last - first).days + 1)]
        values: dict[str, dict] = {day: {} for day in days}
        errors: dict[str, dict] = {day: {} for day in days}
        params = {"startDate": start, "endDate": end}
        endpoints = {
            "summary": ("/usersummary-service/v2/dailysummaries", params, "data", "calendarDate"),
            "sleep": ("/sleep-service/sleep/dailySleepSummariesByDate", params, None, "calendarDate"),
            "hrv": (f"/hrv-service/hrv/daily/{start}/{end}", None, "hrvSummaries", "calendarDate"),
            "body_battery": ("/wellness-service/wellness/bodyBattery/reports/daily", params, None, "date"),
        }
        for kind, (path, query, wrapper, date_key) in endpoints.items():
            try:
                rows = self._records(self.get(path, query), wrapper)
                seen = set()
                for row in rows:
                    day = row.get(date_key)
                    if day not in values:
                        continue
                    if day in seen:
                        raise PersonalApiError("Personal API returned duplicate daily dates")
                    seen.add(day)
                    record = self._summary(row) if kind == "summary" else row
                    values[day][kind] = [record] if kind == "body_battery" else record
                for day in days:
                    if day not in seen:
                        errors[day][kind] = "No data returned for this date"
            except Exception as exc:
                # No partial records from a malformed batch are committed for this category.
                for day in days:
                    values[day].pop(kind, None)
                    errors[day][kind] = (str(exc) if isinstance(exc, PersonalApiError)
                                         else f"Personal API processing failed ({type(exc).__name__})")
        return values, errors

    def get_activities_by_date(self, start: str, end: str) -> list[dict]:
        activities: list[dict] = []
        seen = set()
        for page in range(100):
            rows = self._records(self.get("/activitylist-service/activities/search/activities",
                {"start": page * 100, "limit": 100, "startDate": start, "endDate": end}), None)
            for row in rows:
                activity_id = row.get("activityId")
                if not activity_id or activity_id in seen:
                    raise PersonalApiError("Personal API returned missing or repeated activity IDs")
                seen.add(activity_id)
                activities.append(row)
            if len(rows) < 100:
                return activities
        raise PersonalApiError("Personal API activity pagination exceeded 100 pages; sync is incomplete")
