---
name: setup
description: Guide the user through installing and connecting their own Garmin China Sync Cloud Worker.
---

# Set up Garmin China Sync Cloud

Help the user install the repository's Cloud Edition. Each user must deploy their own Cloudflare Worker and connect their own Garmin China Personal API Key. The marketplace package provides setup and interpretation guidance; it does not contain a shared MCP endpoint.

## Setup path

1. Point the user to the repository's `cloud/README.md` for the full PowerShell instructions.
2. Help them deploy `cloud/worker` to their Cloudflare account and create/bind their own `OAUTH_KV` namespace.
3. Ask them to copy the Worker HTTPS URL from Wrangler. Never ask them to paste their Garmin Key into chat or a config file.
4. Have them add a remote MCP server in the client they use. The URL is `https://<their-worker>.<their-account>.workers.dev/mcp`, with OAuth authentication.
5. They enter the Garmin Personal API Key only on the HTTPS authorization page.
6. Once the client exposes `garmin_get_daily`, `garmin_get_activities`, and `garmin_get_activity_detail`, use those connected tools to answer data questions.

Do not claim that the setup plugin itself has connected Garmin data tools. If the user asks for live Garmin data before adding their MCP endpoint, explain that the endpoint must be connected first.

## Data interpretation

- Use only tool results returned in the current conversation. State missing dates and fields.
- Bound queries to the available tools: daily data supports at most 31 days; activity lists support at most 366 days and 100 records.
- Do not claim activity summaries include GPS tracks or per-second samples.
- Never ask for, repeat, or expose the Personal API Key, access token, or OAuth code.
- Explain health measurements informationally; do not diagnose or present training advice as medical care.
