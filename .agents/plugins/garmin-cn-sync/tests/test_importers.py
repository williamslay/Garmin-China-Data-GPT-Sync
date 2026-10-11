from pathlib import Path

from garmin_cn_sync.database import Database
from garmin_cn_sync.importers import import_directory


TCX = """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities><Activity Sport="Running"><Id>2026-09-14T01:00:00Z</Id>
  <Lap><TotalTimeSeconds>1800</TotalTimeSeconds><DistanceMeters>5000</DistanceMeters><Calories>300</Calories></Lap>
  </Activity></Activities>
</TrainingCenterDatabase>
"""


def test_tcx_import(tmp_path: Path) -> None:
    imports = tmp_path / "imports"
    imports.mkdir()
    (imports / "run.tcx").write_text(TCX, encoding="utf-8")
    db = Database(tmp_path / "db.sqlite3")
    result = import_directory(db, imports)
    assert result["imported"] == 1
    assert db.status()["activity_records"] == 1
