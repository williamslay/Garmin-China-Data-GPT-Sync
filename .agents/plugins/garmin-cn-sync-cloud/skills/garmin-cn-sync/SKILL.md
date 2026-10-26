---
name: garmin-cn-sync
description: Interpret Garmin China daily health, sleep, HRV, Body Battery, and activity data from the connected personal MCP server.
---

Use the user's connected Garmin China Sync MCP server when a request asks about their Garmin health or activity records. Available read-only tools are:

- `garmin_get_daily`: daily summary, sleep, HRV, and Body Battery for 1–31 days.
- `garmin_get_activities`: activity list for 1–366 days, up to 100 records.
- `garmin_get_activity_detail`: one activity's summary/detail by positive numeric ID.

Retrieve only the minimum date range needed. State missing dates/fields and distinguish Garmin measurements from interpretation. Activity summary/detail responses may omit GPS tracks and per-second samples. Never request, repeat, or expose the user's Personal API Key or tokens. Health interpretations are informational, not diagnoses.
