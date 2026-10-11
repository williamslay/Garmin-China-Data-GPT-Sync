from __future__ import annotations

import logging
import threading

from mcp.server.fastmcp import FastMCP

from .config import sync_interval_seconds
from .service import GarminService


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
LOGGER = logging.getLogger("garmin-cn-sync")
mcp = FastMCP("Garmin China Sync")
SERVICE = GarminService()


@mcp.tool()
def garmin_status() -> dict:
    """Show local Garmin China connection, database, and last-sync status."""
    return SERVICE.status()


@mcp.tool()
def garmin_sync_now(health_days: int = 2, activity_days: int = 7) -> dict:
    """Read Garmin China data and update local cache. Never writes to Garmin."""
    return SERVICE.sync_now(health_days=health_days, activity_days=activity_days)


@mcp.tool()
def garmin_get_daily(start_date: str, end_date: str, include_raw: bool = False) -> list[dict]:
    """Read cached daily health, sleep, HRV, stress, steps, and Body Battery data."""
    return SERVICE.daily(start_date, end_date, include_raw=include_raw)


@mcp.tool()
def garmin_get_activities(start_date: str, end_date: str, limit: int = 100) -> list[dict]:
    """Read cached Garmin activities between YYYY-MM-DD dates."""
    return SERVICE.activities(start_date, end_date, limit=limit)


@mcp.tool()
def garmin_get_trends(days: int = 28) -> dict:
    """Calculate local trend summaries from cached health data."""
    return SERVICE.trends(days=days)


@mcp.tool()
def garmin_import_files() -> dict:
    """Import FIT and TCX files from the configured local import directory."""
    return SERVICE.import_files()


def _scheduler(stop: threading.Event) -> None:
    interval = sync_interval_seconds()
    if stop.wait(30):
        return
    while not stop.is_set():
        try:
            if SERVICE.status()["credentials_configured"]:
                SERVICE.sync_now(health_days=2, activity_days=7)
        except Exception:
            LOGGER.exception("Scheduled Garmin China sync failed")
        stop.wait(interval)


def main() -> None:
    stop = threading.Event()
    worker = threading.Thread(target=_scheduler, args=(stop,), name="garmin-cn-hourly-sync", daemon=True)
    worker.start()
    try:
        mcp.run(transport="stdio")
    finally:
        stop.set()


if __name__ == "__main__":
    main()
