---
name: garmin-cn-sync
description: Use local Garmin China garmin.cn health and activity data through Garmin China Sync MCP tools. Trigger for Garmin China data, sleep, HRV, Body Battery, heart-rate, stress, steps, activity, workout-history, and fitness-trend questions.
---

# Garmin China Sync

Use only read-only tools. Never ask user to paste Garmin password, MFA code, cookies, or tokens
into chat. Save Personal API keys locally through `scripts/authenticate-personal.ps1`;
legacy web login uses `scripts/authenticate.ps1`.

1. Call `garmin_status` before data work.
2. If cache is older than one hour, call `garmin_sync_now` with smallest useful range.
3. Use `garmin_get_daily` for health, sleep, HRV, stress, and Body Battery questions.
4. Use `garmin_get_activities` for activity questions.
5. Use `garmin_get_trends` only after confirming enough cached daily records exist.
6. Use `garmin_import_files` only after user places FIT/TCX files in reported import directory.

Use `provider` and the last-sync metadata to identify the active source: `personal-api` is the official
China Personal API; `china-web` uses unofficial web endpoints. Historical cache may contain both.
Treat health and location data as sensitive. Do not expose raw payloads unless explicitly requested.
Personal API may omit activity VO2max. `_retained_field_sources` identifies values preserved from a
previous fetch of the same activity; never substitute another activity's VO2max for a missing value.
