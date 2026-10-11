from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "GarminCnSync"
KEYRING_SERVICE = "GarminCnSync"


def app_dir() -> Path:
    root = os.getenv("LOCALAPPDATA")
    base = Path(root) if root else Path.home() / ".local" / "share"
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    override = os.getenv("GARMIN_CN_SYNC_DB")
    return Path(override).expanduser().resolve() if override else app_dir() / "garmin-cn-sync.sqlite3"


def import_dir() -> Path:
    override = os.getenv("GARMIN_CN_SYNC_IMPORT_DIR")
    path = Path(override).expanduser().resolve() if override else app_dir() / "imports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sync_interval_seconds() -> int:
    try:
        value = int(os.getenv("GARMIN_CN_SYNC_INTERVAL_SECONDS", "3600"))
    except ValueError:
        return 3600
    return max(900, value)
