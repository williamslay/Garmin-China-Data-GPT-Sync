# Garmin China Sync Cloud

Use the connected user's own Garmin China account through the deployed remote MCP server. All tools are read-only. The user deploys their own Cloudflare Worker and authorizes it with a Garmin China Personal API Key in the browser OAuth flow.

- `garmin_get_daily`: daily summary, sleep, HRV, Body Battery for up to 31 days.
- `garmin_get_activities`: activity records for up to 366 days, maximum 100 records.
- `garmin_get_activity_detail`: one activity summary/detail object by numeric activity ID.

Interpret only returned measurements. State missing data explicitly. Do not claim that a summary endpoint includes GPS tracks or per-second samples. Do not request, repeat, or expose the user's Personal API Key. For longer trends, retrieve bounded date ranges and summarize transparently. Health interpretations are informational, not medical advice.
