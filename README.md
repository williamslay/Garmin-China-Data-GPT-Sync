# Garmin China Sync

[简体中文](#简体中文) · [English](#english)

## 简体中文

Garmin China Sync 是一个面向 Codex 与兼容 MCP 客户端的本地插件，用于读取 Garmin 中国区（`garmin.cn`）账户中的健康摘要、睡眠、HRV、Body Battery 和运动活动，并将数据缓存到本机，供用户查询与分析。

它只对 Garmin 账户执行读取操作；同步和导入会写入本机 SQLite 缓存，不会修改 Garmin 账户数据。

### 当前支持的功能

- **健康与睡眠日数据**：按日期同步并查询 Garmin 每日统计、睡眠、HRV 与 Body Battery 响应。精简查询可返回步数、静息/最低心率、平均压力、睡眠时长与睡眠分数、前一晚平均 HRV，以及同步错误和时间戳；也可按需读取缓存的原始响应。
- **运动活动历史**：按日期范围查询活动。首次初始化最多回填 365 天；常规同步默认抓取最近 7 天。完整活动响应保存在本机缓存中。
- **趋势汇总**：对最近 2–366 天缓存中可用的步数、静息心率、平均压力、睡眠时长、睡眠分数和前一晚平均 HRV 计算均值，并给出前、后半段均值。它是描述性统计，不是医学判断或训练处方。
- **FIT / TCX 文件导入**：从本机导入目录读取顶层 `.fit` 和 `.tcx` 文件，将可解析的活动摘要写入活动缓存；原文件不会被删除或移动。
- **状态与错误可见性**：查看账户凭据是否已配置、缓存路径与记录数、最近一次同步结果；某些接口失败时保留其他已成功数据，并报告部分同步错误。
- **定时增量同步**：MCP 服务器运行时，在启动约 30 秒后开始检查；默认每小时同步最近 2 天健康数据和 7 天活动数据。只有本地凭据已配置时才会自动同步。

### 可用 MCP 工具

| 工具 | 用途 |
| --- | --- |
| `garmin_status` | 查看中国区连接状态、本地数据库、记录数量和最近同步结果。 |
| `garmin_sync_now` | 立即同步；默认 `health_days=2`、`activity_days=7`。健康范围支持 1–31 天，活动范围支持 1–366 天。 |
| `garmin_get_daily` | 查询日期范围内缓存的每日健康、睡眠、HRV 和 Body Battery 数据；可用 `include_raw=true` 请求原始缓存响应。 |
| `garmin_get_activities` | 按 `YYYY-MM-DD` 日期范围读取缓存活动；`limit` 支持 1–500。 |
| `garmin_get_trends` | 计算 2–366 天缓存数据的描述性趋势均值。 |
| `garmin_import_files` | 扫描配置的本机目录并导入 FIT / TCX 活动文件。 |

### 首次安装与初始化

当前社区发布以 Windows 10/11 为目标环境，需要 PowerShell 7、Python 3.12+ 和 Garmin 中国区账户。通过 Codex CLI 添加 GitHub marketplace：

```powershell
codex plugin marketplace add williamslay/Garmin-China-Data-GPT-Sync --ref main --sparse .agents/plugins
```

在 Codex 桌面端安装 `Garmin China Sync` 后，在本机 PowerShell 7 终端进入插件目录并运行：

```powershell
Set-Location .agents/plugins/garmin-cn-sync
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\setup.ps1
pwsh -NoLogo -NoProfile -File .\scripts\authenticate.ps1
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\bootstrap.ps1
```

首次初始化默认回填最近 **30 天健康日数据** 和 **365 天活动历史**。后续 MCP 服务器运行时按默认间隔增量同步。更多设置、目录与故障说明见[插件使用说明](.agents/plugins/garmin-cn-sync/README.md)。

### 数据位置、隐私与限制

- Garmin 邮箱、密码与刷新令牌通过 `keyring` 存入操作系统凭据库；Windows 上为 Windows Credential Manager。
- 健康与活动缓存保存在本机 SQLite：`%LOCALAPPDATA%\GarminCnSync\garmin-cn-sync.sqlite3`。
- FIT / TCX 导入目录默认为 `%LOCALAPPDATA%\GarminCnSync\imports`。导入文件仍保留在原目录。
- MCP 服务在本机运行。凭据不会放进聊天；工具返回的数据会提供给发起请求的 MCP 客户端，以完成用户要求的查询或分析。请同时遵循所用客户端的数据处理设置。
- 当前使用**非官方** Garmin Connect Web 客户端和接口；Garmin 可能随时更改或限制访问。本项目不是 Garmin 官方集成，使用前请确认你有权访问该账户并自行审阅适用条款。
- 插件没有修改 Garmin 账户的工具；不保证接口可用性；不是医疗设备，不提供诊断。

可通过 `GARMIN_CN_SYNC_DB`、`GARMIN_CN_SYNC_IMPORT_DIR` 和 `GARMIN_CN_SYNC_INTERVAL_SECONDS` 指定本地数据库、导入目录和同步间隔；同步间隔最低为 900 秒。

### 许可证

本项目采用 MIT License，详见 [LICENSE](LICENSE)。

## English

Garmin China Sync is a local-first plugin for Codex and compatible MCP clients. It reads health summaries, sleep, HRV, Body Battery, and activity history from Garmin China (`garmin.cn`), caches the responses in a local SQLite database, and makes the cached data available for user-requested queries and analysis.

The integration only reads from the Garmin account. Syncing and file import write to the local cache; they do not modify Garmin account data.

### Current capabilities

- **Daily health and sleep data:** Sync and query Garmin daily stats, sleep, HRV, and Body Battery responses by date. Compact results include steps, resting/minimum heart rate, average stress, sleep duration and score, last-night average HRV, errors, and sync timestamps. Raw cached responses can be requested when needed.
- **Activity history:** Query cached activities by date range. Initial bootstrap fetches up to 365 days; regular sync defaults to the latest 7 days. Full activity responses are cached locally.
- **Trend summaries:** Calculate averages for available steps, resting heart rate, average stress, sleep duration, sleep score, and last-night average HRV over 2–366 days, including averages for the first and second halves of the returned data. These are descriptive statistics, not medical assessments or training prescriptions.
- **FIT / TCX import:** Read top-level `.fit` and `.tcx` files from a local import directory and add parseable activity summaries to the local cache. Source files are not deleted or moved.
- **Status and error reporting:** Inspect credential configuration, cache location and record counts, and the latest sync result. If one endpoint fails, successful data is retained and partial errors are reported.
- **Scheduled incremental sync:** While the MCP server is running, it starts checking about 30 seconds after launch and syncs the latest 2 health days and 7 activity days hourly by default. Automatic sync runs only when local credentials are configured.

### MCP tools

| Tool | Purpose |
| --- | --- |
| `garmin_status` | Show China-region connection status, local database information, record counts, and the latest sync result. |
| `garmin_sync_now` | Sync immediately; defaults to `health_days=2` and `activity_days=7`. Health supports 1–31 days; activities support 1–366 days. |
| `garmin_get_daily` | Read cached daily health, sleep, HRV, and Body Battery data; set `include_raw=true` to request raw cached responses. |
| `garmin_get_activities` | Read cached activities for a `YYYY-MM-DD` date range; `limit` is 1–500. |
| `garmin_get_trends` | Calculate descriptive averages for 2–366 days of cached data. |
| `garmin_import_files` | Scan the configured local directory and import FIT / TCX activity files. |

### Install and initialize

The current community distribution targets Windows 10/11 and requires PowerShell 7, Python 3.12+, and a Garmin China account. Add the GitHub marketplace with Codex CLI:

```powershell
codex plugin marketplace add williamslay/Garmin-China-Data-GPT-Sync --ref main --sparse .agents/plugins
```

Install `Garmin China Sync` in the Codex desktop app, then run the following in a local PowerShell 7 terminal:

```powershell
Set-Location .agents/plugins/garmin-cn-sync
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\setup.ps1
pwsh -NoLogo -NoProfile -File .\scripts\authenticate.ps1
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\bootstrap.ps1
```

The initial bootstrap fetches up to **30 days of daily health data** and **365 days of activity history**. See the [plugin guide](.agents/plugins/garmin-cn-sync/README.md) for storage locations, configuration, and troubleshooting.

### Privacy and limitations

- Garmin email, password, and refresh tokens are stored with `keyring` in the operating system credential vault (Windows Credential Manager on Windows).
- Health and activity data is cached in local SQLite at `%LOCALAPPDATA%\GarminCnSync\garmin-cn-sync.sqlite3`.
- FIT / TCX files are read from `%LOCALAPPDATA%\GarminCnSync\imports` by default and remain in place after import.
- The MCP server runs locally. Credentials are not placed in chat; tool results are returned to the requesting MCP client for the query or analysis. Review the data-handling settings of that client as well.
- This project currently relies on an **unofficial** Garmin Connect web client and endpoints. Garmin may change or restrict access. This is not an official Garmin integration; use only with an account you are authorized to access and review applicable terms.
- The plugin has no Garmin account-write tools, availability is not guaranteed, and it is not a medical device or diagnostic service.

Optional environment variables: `GARMIN_CN_SYNC_DB`, `GARMIN_CN_SYNC_IMPORT_DIR`, and `GARMIN_CN_SYNC_INTERVAL_SECONDS` (minimum 900 seconds).

### License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
