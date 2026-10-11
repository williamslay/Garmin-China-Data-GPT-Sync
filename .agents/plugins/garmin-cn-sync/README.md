# Garmin China Sync

[简体中文](#简体中文) · [English](#english)

## 简体中文

Garmin China Sync 是一个本地运行的 MCP 插件，将 Garmin 中国区（`garmin.cn`）中的健康日数据和运动活动同步到本机 SQLite 缓存，供 Codex 或其他兼容 MCP 的客户端按需查询。插件面向 Windows 10/11，当前发布版本为 `0.1.0`。

**重要边界：**插件对 Garmin 账户只执行读取，不提供修改账户数据的功能；但同步会在本机更新缓存。它使用非官方 Garmin Connect Web 客户端，不是 Garmin 官方集成，接口可能变化或被限制。

### 功能说明

#### 健康、睡眠与恢复数据

同步器逐日读取 Garmin 的每日统计、睡眠、HRV 和 Body Battery 接口，并把各接口响应保存在本地。可用信息取决于 Garmin 账户、设备和 API 当日是否提供数据。`garmin_get_daily` 默认返回较精简的字段：

- 步数；
- 静息心率（若该字段缺失，代码会回退到当日最低心率，因此结果也可能是最低心率）；
- 平均压力；
- 睡眠时长（秒）和睡眠分数；
- 前一晚平均 HRV；
- Body Battery 接口返回值、逐日错误信息和同步时间。

若分析需要接口原始结构，可通过 `include_raw=true` 读取缓存的原始响应。原始数据不一定每日齐全，接口失败会体现在该日期的 `errors` 中；服务不会因为某个接口失败就丢弃其他成功数据。

#### 活动历史与本地文件导入

- Garmin 活动按起止日期范围同步并保存在本地；活动工具返回活动标识、时间、类型、名称和原始活动响应。
- 首次初始化最多请求 365 天活动历史；常规同步默认刷新最近 7 天，以覆盖新活动和近期更新。
- FIT / TCX 导入器扫描导入目录的**当前层级**（不递归子目录），读取 `.fit` 与 `.tcx` 文件。支持的摘要字段取决于文件内容，通常包括活动类型、开始时间、距离、时长和卡路里；FIT 还会提取平均/最高心率（若文件提供）。
- 导入器不移动或删除源文件；导入的活动摘要会写入同一个 SQLite 活动缓存。修改同一文件内容会生成新的文件哈希活动 ID。

#### 趋势与状态

`garmin_get_trends` 对最近 2–366 个日历日的**已有缓存数据**计算步数、静息心率、平均压力、睡眠时长、睡眠分数和前一晚平均 HRV 的均值，并提供返回记录序列前半段/后半段的均值及有效样本数。它是简单描述统计，不做插值、医学判断或训练计划建议。

`garmin_status` 显示地区（`garmin.cn`）、是否已配置凭据、本地数据库路径、每日记录数、活动记录数、最近一次同步结果和导入目录。一次同步可为 `ok`、`partial` 或 `failed`；`partial` 表示部分接口失败，成功取得的数据仍会保存。

### MCP 工具一览

| 工具 | 作用与参数 |
| --- | --- |
| `garmin_status` | 检查本地配置、缓存和最近同步状态。 |
| `garmin_sync_now(health_days=2, activity_days=7)` | 立即同步。健康日期范围为 1–31 天，活动历史范围为 1–366 天。 |
| `garmin_get_daily(start_date, end_date, include_raw=false)` | 读取指定日期区间的每日缓存。日期格式为 `YYYY-MM-DD`；默认返回精简字段，`include_raw=true` 返回原始响应。 |
| `garmin_get_activities(start_date, end_date, limit=100)` | 读取指定日期区间活动；`limit` 范围为 1–500。 |
| `garmin_get_trends(days=28)` | 汇总最近 2–366 天的可用缓存指标。 |
| `garmin_import_files()` | 扫描当前配置目录中的 FIT/TCX 文件并导入活动。 |

日期区间按含首尾日期处理。查询只返回本机缓存里已有的数据，不会自动为缺失日期补空记录。MCP 客户端可能会在读取、同步或导入前请求用户批准。

### 安装、认证与首次同步

#### 环境要求

- Windows 10 或 Windows 11
- PowerShell 7，且 `pwsh` 可从 `PATH` 找到
- Python 3.12 或更新版本（推荐 `py -3.12`）
- 有权使用的 Garmin 中国区账户
- Codex 桌面端或兼容 MCP 的客户端

#### 从 GitHub marketplace 安装

先在 Codex CLI 中添加 marketplace，并在 Codex 桌面端安装插件：

```powershell
codex plugin marketplace add williamslay/Garmin-China-Data-GPT-Sync --ref main --sparse .agents/plugins
```

也可以克隆仓库后，在 Codex 桌面端从本地 marketplace 安装。安装后，在 PowerShell 7 终端进入此插件目录（`garmin-cn-sync`）执行：

```powershell
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\setup.ps1
pwsh -NoLogo -NoProfile -File .\scripts\authenticate.ps1
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\bootstrap.ps1
```

`setup.ps1` 会创建 `.venv` 并安装插件及测试依赖。认证脚本在本机交互式提示 Garmin 邮箱、密码和需要时的 MFA 验证码。不要把密码、验证码、Cookie 或 token 发到聊天、Issue 或日志中。认证信息和刷新令牌经 `keyring` 写入 Windows Credential Manager，服务名为 `GarminCnSync`。

`bootstrap.ps1` 首次回填最近最多 **30 天健康日数据** 和 **365 天活动历史**。之后只要 MCP 服务正在运行且本机凭据可用，调度器会在启动约 30 秒后开始按间隔同步最近 2 天健康数据和 7 天活动数据。默认间隔为 3600 秒（约 1 小时），最小为 900 秒（15 分钟）；服务停止期间不会执行定时同步。

### 本地数据与可选配置

- SQLite 数据库：`%LOCALAPPDATA%\GarminCnSync\garmin-cn-sync.sqlite3`
- FIT/TCX 导入目录：`%LOCALAPPDATA%\GarminCnSync\imports`
- 登录凭据与 token：Windows Credential Manager，服务名 `GarminCnSync`

可以通过环境变量覆盖默认值：

| 环境变量 | 用途 |
| --- | --- |
| `GARMIN_CN_SYNC_DB` | SQLite 数据库完整路径。 |
| `GARMIN_CN_SYNC_IMPORT_DIR` | FIT/TCX 导入目录。 |
| `GARMIN_CN_SYNC_INTERVAL_SECONDS` | 定时同步间隔秒数，最小 900；非法值回退到 3600。 |

MCP 服务器与缓存运行在本机；凭据不会放入聊天。用户请求的数据会由 MCP 工具返回给调用客户端，以完成该次查询或分析，因此也请检查客户端自身的数据处理设置。

### 限制与责任

- 当前通过 `garminconnect` 的非官方 Garmin Connect Web 接口访问中国区账户。Garmin 可能更改、限制或停止这些接口，本项目不保证持续可用。
- 仅用于你有权访问的账户，并由使用者自行确认 Garmin 适用条款和当地要求。
- 插件只读取 Garmin，不会更改账户设置或运动数据；本地同步/导入会写入 SQLite 缓存。
- 运动与健康数值仅供个人信息整理，不是医疗设备、诊断或治疗建议。

### 开发与测试

在插件目录运行：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

测试使用合成数据，不会自动登录真实 Garmin 账户或执行真实同步。

## English

Garmin China Sync is a locally running MCP plugin that syncs Garmin China (`garmin.cn`) daily health data and activities to a local SQLite cache for on-demand queries from Codex or another compatible MCP client. The current release targets Windows 10/11 and is version `0.1.0`.

**Important boundary:** the plugin only reads from the Garmin account and does not provide account-write operations; sync updates the local cache. It relies on an unofficial Garmin Connect web client, not an official Garmin integration, and the endpoints may change or be restricted.

### Features

- **Daily health, sleep, and recovery data:** Reads daily stats, sleep, HRV, and Body Battery responses. Compact daily results include steps, resting heart rate (falling back to minimum heart rate when that field is absent), average stress, sleep duration and score, last-night average HRV, Body Battery response, per-day errors, and sync time. Raw cached responses can be requested with `include_raw=true`.
- **Activity history:** Syncs and queries activities by date range. Initial bootstrap requests up to 365 days; regular sync defaults to the latest 7 days. Full activity responses are cached locally.
- **FIT / TCX imports:** Scans the top level of the configured local directory (not recursively) for `.fit` and `.tcx` files. Depending on file contents, it imports activity type, start time, distance, duration, and calories; FIT files may also provide average and maximum heart rate. Source files remain in place.
- **Trend summaries:** Calculates means and valid sample counts for available steps, resting heart rate, average stress, sleep duration, sleep score, and last-night average HRV over 2–366 calendar days, with means for the first and second halves of the returned cached records. This is simple descriptive statistics—not interpolation, medical assessment, or training advice.
- **Status and partial errors:** Shows region, whether credentials are configured, local database path and record counts, import directory, and latest sync result. A partial failure is reported while successfully retrieved data is retained.
- **Scheduled incremental sync:** While the MCP server is running and credentials are configured, the scheduler starts about 30 seconds after launch and syncs the latest 2 health days and 7 activity days by default. The default interval is 3,600 seconds; the minimum is 900 seconds.

### MCP tools

| Tool | Purpose and parameters |
| --- | --- |
| `garmin_status` | Inspect local configuration, cache, and latest sync status. |
| `garmin_sync_now(health_days=2, activity_days=7)` | Sync now; health range is 1–31 days and activity range is 1–366 days. |
| `garmin_get_daily(start_date, end_date, include_raw=false)` | Read cached daily data for `YYYY-MM-DD` dates; optionally return raw responses. |
| `garmin_get_activities(start_date, end_date, limit=100)` | Read cached activities for a date range; `limit` is 1–500. |
| `garmin_get_trends(days=28)` | Summarize available cached metrics for 2–366 days. |
| `garmin_import_files()` | Scan the configured directory and import FIT/TCX activities. |

Date ranges include both endpoints. Queries return records already present in the local cache and do not synthesize rows for missing dates. An MCP client may ask for approval before reading, syncing, or importing.

### Installation and first sync

#### Requirements

- Windows 10 or 11
- PowerShell 7 with `pwsh` on `PATH`
- Python 3.12 or newer (`py -3.12` recommended)
- A Garmin China account you are authorized to access
- Codex desktop or a compatible MCP client

#### Install from the GitHub marketplace

Add the marketplace with Codex CLI, then install the plugin in the Codex desktop app:

```powershell
codex plugin marketplace add williamslay/Garmin-China-Data-GPT-Sync --ref main --sparse .agents/plugins
```

Alternatively, clone the repository and install from its local marketplace. After installation, open a PowerShell 7 terminal in this plugin directory (`garmin-cn-sync`) and run:

```powershell
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\setup.ps1
pwsh -NoLogo -NoProfile -File .\scripts\authenticate.ps1
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\bootstrap.ps1
```

`setup.ps1` creates `.venv` and installs the plugin and test dependencies. The local interactive authentication script prompts for Garmin email, password, and an MFA code if required. Never put passwords, MFA codes, cookies, or tokens in chat, issues, or logs. Credentials and refresh tokens are stored through `keyring` in Windows Credential Manager under service name `GarminCnSync`.

The initial bootstrap requests up to **30 days of daily health data** and **365 days of activity history**. While the MCP server is running with credentials configured, the scheduler begins about 30 seconds after launch and syncs the latest 2 health days and 7 activity days. The default interval is 3,600 seconds (about one hour), with a 900-second (15-minute) minimum. Scheduled sync does not run while the server is stopped.

### Local storage and configuration

- SQLite database: `%LOCALAPPDATA%\GarminCnSync\garmin-cn-sync.sqlite3`
- FIT/TCX import directory: `%LOCALAPPDATA%\GarminCnSync\imports`
- Credentials and tokens: Windows Credential Manager, service name `GarminCnSync`

Optional environment variables:

| Variable | Purpose |
| --- | --- |
| `GARMIN_CN_SYNC_DB` | Full path to the SQLite database. |
| `GARMIN_CN_SYNC_IMPORT_DIR` | FIT/TCX import directory. |
| `GARMIN_CN_SYNC_INTERVAL_SECONDS` | Scheduled sync interval in seconds; minimum 900, invalid values fall back to 3600. |

The MCP server and cache run locally, and credentials are not placed in chat. Data requested through an MCP tool is returned to the calling client for that query or analysis; review that client's own data-handling settings as well.

### Limitations and responsibility

- Access to Garmin China currently relies on the unofficial Garmin Connect web client. Garmin may change, restrict, or discontinue these endpoints; continued availability is not guaranteed.
- Use only with an account you are authorized to access, and review applicable Garmin terms and local requirements.
- The plugin reads from Garmin and does not change account settings or activity data; local sync/import writes to the SQLite cache.
- Health and fitness information is for personal data organization only, not a medical device, diagnosis, or treatment advice.

### Development and tests

Run from the plugin directory:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use synthetic data and never log in to a real Garmin account or run a live sync automatically.
