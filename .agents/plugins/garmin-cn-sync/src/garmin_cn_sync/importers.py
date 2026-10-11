from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from .database import Database


ALLOWED_SUFFIXES = {".fit", ".tcx"}


def _file_id(path: Path) -> str:
    return "file-" + hashlib.sha256(path.read_bytes()).hexdigest()[:24]


def parse_tcx(path: Path) -> dict[str, Any]:
    root = ElementTree.parse(path).getroot()
    activity = next((node for node in root.iter() if node.tag.endswith("Activity")), None)
    if activity is None:
        raise ValueError("TCX contains no Activity element")
    identifier = next((node.text for node in activity.iter() if node.tag.endswith("Id") and node.text), None)
    totals: dict[str, Any] = {}
    for node in activity.iter():
        if node.text is None:
            continue
        if node.tag.endswith("TotalTimeSeconds"):
            totals["duration"] = float(node.text)
        elif node.tag.endswith("DistanceMeters") and "distance" not in totals:
            totals["distance"] = float(node.text)
        elif node.tag.endswith("Calories") and "calories" not in totals:
            totals["calories"] = int(node.text)
    return {"activityId": _file_id(path), "activityName": path.stem,
            "activityType": {"typeKey": activity.attrib.get("Sport", "unknown").lower()},
            "startTimeLocal": identifier or datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            "sourceFile": str(path), **totals}


def parse_fit(path: Path) -> dict[str, Any]:
    from fitparse import FitFile
    fit = FitFile(path)
    values: dict[str, Any] = {}
    for message in fit.get_messages("session"):
        values = {field.name: field.value for field in message}
        break
    if not values:
        raise ValueError("FIT contains no session message")
    start = values.get("start_time")
    if hasattr(start, "isoformat"):
        start = start.isoformat()
    sport = values.get("sport") or values.get("sub_sport") or "unknown"
    return {"activityId": _file_id(path), "activityName": path.stem,
            "activityType": {"typeKey": str(sport)},
            "startTimeLocal": start or datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            "sourceFile": str(path), "distance": values.get("total_distance"),
            "duration": values.get("total_timer_time") or values.get("total_elapsed_time"),
            "calories": values.get("total_calories"), "averageHR": values.get("avg_heart_rate"),
            "maxHR": values.get("max_heart_rate")}


def import_directory(database: Database, directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []
    errors: dict[str, str] = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        try:
            activity = parse_fit(path) if path.suffix.lower() == ".fit" else parse_tcx(path)
            imported.append(database.upsert_activity(activity, source="file-import"))
        except Exception as exc:
            errors[path.name] = f"{type(exc).__name__}: {exc}"[:500]
    return {"directory": str(directory), "imported": len(imported), "activity_ids": imported, "errors": errors}
