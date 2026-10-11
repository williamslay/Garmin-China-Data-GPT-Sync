# Garmin China Sync

A local-first, read-only Codex plugin for syncing and querying Garmin China health and activity data. The installable plugin and GitHub marketplace catalog are under [`.agents/plugins`](.agents/plugins/marketplace.json).

## Install from GitHub

In Codex CLI, add this repository as a plugin marketplace (replace the placeholders with the published GitHub owner and repository):

```powershell
codex plugin marketplace add OWNER/REPOSITORY --ref main --sparse .agents/plugins
```

Alternatively, clone the repository and follow the [plugin setup guide](.agents/plugins/garmin-cn-sync/README.md). You will need to install the plugin from the marketplace in the Codex desktop app, then run its setup and authentication scripts in a local terminal.

## Scope and privacy

The MCP server runs locally. Garmin credentials stay in the user's OS credential store and cached health/activity data stays in a local SQLite database. The project currently uses an unofficial Garmin Connect web client, so it is intended for personal/local use; it is not an approved Garmin integration and is not suitable for OpenAI's public plugin directory in its current form.

See [the plugin README](.agents/plugins/garmin-cn-sync/README.md) for requirements, limitations, storage locations, and setup instructions.
