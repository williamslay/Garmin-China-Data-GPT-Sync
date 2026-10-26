# Garmin China Sync Cloud marketplace plugin

This Codex repository-marketplace plugin includes setup and data-interpretation skills. It does not bundle a shared Garmin service because every user deploys their own Cloudflare Worker and gets a different MCP URL.

## Install

Add this GitHub repository as a marketplace, then install **Garmin China Sync Cloud** from the Plugins Directory:

```powershell
codex plugin marketplace add williamslay/Garmin-China-Data-GPT-Sync --ref main
```

After installation, use the Setup skill or follow `cloud/README.md` in the repository to deploy your Worker. Then add your own remote MCP server to the client:

```text
https://<your-worker>.<your-account>.workers.dev/mcp
```

Choose OAuth. Enter the Garmin Personal API Key only on the HTTPS authorization page. Do not paste it into chat or a plugin configuration file.

The tool calls become available only after the user's remote MCP endpoint is connected. For data boundaries and privacy details, see `cloud/README.md`, `cloud/PRIVACY.md`, and `cloud/TERMS.md` in the repository.
