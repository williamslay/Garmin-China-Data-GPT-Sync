# Garmin China Sync

Local-first, read-only Garmin China (`garmin.cn`) sync for Codex and compatible MCP clients.
This initial community distribution targets Windows 10/11 with PowerShell 7 and Python 3.12+.

## Important limitations and data handling

- This project uses an unofficial Garmin Connect web client. Garmin may change or restrict the endpoints; availability is not guaranteed. Use only with an account you are authorized to access and review Garmin's applicable terms before use.
- The plugin has no Garmin account-write tools. It reads account data and stores the cache on the user's computer.
- Credentials and refresh tokens are stored in the operating-system credential vault through `keyring`; on Windows this is Windows Credential Manager. Health/activity data is stored in a local SQLite database.
- Never paste passwords, MFA codes, cookies, or tokens into a chat, issue, or log. Authenticate only in the local interactive terminal.
- This is not a medical device and does not provide a diagnosis.

## Requirements

- Windows 10 or 11
- PowerShell 7 (`pwsh`) available on `PATH`
- Python 3.12 or newer (`py -3.12` recommended)
- A Garmin China account

## Install and authenticate

From this plugin directory, run these commands in a PowerShell 7 terminal:

```powershell
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\setup.ps1
pwsh -NoLogo -NoProfile -File .\scripts\authenticate.ps1
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\bootstrap.ps1
```

Authentication is interactive and stays on the user's computer. Bootstrap imports up to 30 days of health data and 365 days of activity history. When the MCP server is running, it incrementally syncs the latest two health days and seven activity days about once per hour.

## Local storage

- Database: `%LOCALAPPDATA%\GarminCnSync\garmin-cn-sync.sqlite3`
- FIT/TCX import directory: `%LOCALAPPDATA%\GarminCnSync\imports`
- Credentials: Windows Credential Manager, service name `GarminCnSync`

Optional environment variables: `GARMIN_CN_SYNC_DB`, `GARMIN_CN_SYNC_IMPORT_DIR`, and `GARMIN_CN_SYNC_INTERVAL_SECONDS` (minimum 900 seconds).

## Available tools

`garmin_status`, `garmin_sync_now`, `garmin_get_daily`, `garmin_get_activities`, `garmin_get_trends`, and `garmin_import_files`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use synthetic data; real-account authentication and sync are never run automatically.
