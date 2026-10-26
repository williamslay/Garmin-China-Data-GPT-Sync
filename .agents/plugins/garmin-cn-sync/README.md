# Garmin China Sync

[简体中文](#简体中文) · [English](#english)

## 简体中文

Garmin China Sync 是一个本地运行的 MCP 插件，将 Garmin 中国区（`garmin.cn`）中的健康日数据和运动活动同步到本机 SQLite 缓存，供 Codex 或其他兼容 MCP 的客户端按需查询。插件面向 Windows 10/11，当前版本为 `0.2.0`。

插件提供官方 **Personal API** 和原有的非官方中国区网页通道，对 Garmin 健康和活动数据只执行读取；同步更新本机缓存。`auto` 模式下，已保存 Personal API Key 时选用官方通道，否则沿用网页通道。2026-10-26 已验证中国区官方认证、睡眠、HRV、Body Battery 和活动接口可用。

### 功能说明

#### 健康、睡眠与恢复数据

官方通道通过 4 个日期范围请求批量读取每日统计、睡眠摘要、HRV 摘要和 Body Battery；网页通道仍逐日读取。日统计保留官方 v2 字段并附加旧版查询兼容字段。缓存的官方睡眠和 HRV 是摘要，未额外下载逐点曲线。可用信息取决于账户、设备和 API 当日是否提供数据。`garmin_get_daily` 默认返回较精简的字段：

- 步数；
- 静息心率（若该字段缺失，代码会回退到当日最低心率，因此结果也可能是最低心率）；
- 平均压力；
- 睡眠时长（秒）和睡眠分数；
- 前一晚平均 HRV；
- Body Battery 接口返回值、逐日错误信息和同步时间。

若分析需要接口原始结构，可通过 `include_raw=true` 读取缓存的原始响应。原始数据不一定每日齐全，接口失败会体现在该日期的 `errors` 中；服务不会因为某个接口失败就丢弃其他成功数据。

#### 活动历史与本地文件导入

- Garmin 活动按起止日期范围同步并保存在本地；活动工具返回活动标识、时间、类型、名称和原始活动响应。
- 官方活动列表保留训练负荷、训练效果、距离、时长及心率。实测官方活动列表和详情未提供原有的 VO₂max 字段；同一活动此前已缓存的 VO₂max 会保留，并在 `_retained_field_sources` 标注旧来源。新活动缺失的 VO₂max 保持缺失，不从其他活动借用。
- 首次初始化最多请求 365 天活动历史；常规同步默认刷新最近 7 天，以覆盖新活动和近期更新。
- FIT / TCX 导入器扫描导入目录的**当前层级**（不递归子目录），读取 `.fit` 与 `.tcx` 文件。支持的摘要字段取决于文件内容，通常包括活动类型、开始时间、距离、时长和卡路里；FIT 还会提取平均/最高心率（若文件提供）。
- 导入器不移动或删除源文件；导入的活动摘要会写入同一个 SQLite 活动缓存。修改同一文件内容会生成新的文件哈希活动 ID。

#### 趋势与状态

`garmin_get_trends` 对最近 2–366 个日历日的**已有缓存数据**计算步数、静息心率、平均压力、睡眠时长、睡眠分数和前一晚平均 HRV 的均值，并提供返回记录序列前半段/后半段的均值及有效样本数。它是简单描述统计，不做插值、医学判断或训练计划建议。

`garmin_status` 显示地区（`garmin.cn`）、当前 `provider`（`personal-api` 或 `china-web`）、两种凭据各自是否已配置、本地数据库路径、记录数、最近同步结果和导入目录。同步日志也记录数据源。一次同步可为 `ok`、`partial` 或 `failed`；`partial` 表示部分接口失败或某日未返回记录，成功数据仍会保存。

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
pwsh -NoLogo -NoProfile -File .\scripts\authenticate-personal.ps1
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\bootstrap.ps1
```

`setup.ps1` 会创建 `.venv` 并安装依赖。先在[中国区 Personal API 页面](https://connect.garmin.cn/app/settings/personalApiToken)创建自己的 Key，再运行 `authenticate-personal.ps1`，在本机隐藏输入中录入。Key 存在 Windows Credential Manager 的 `GarminCnSync / personal-api-key-cn`；Bearer token 分块存在独立的 `GarminCnSync.PersonalApi.CN` 服务中，并在临近过期时重新交换。接口返回 401 时仅刷新重试一次，其他错误会报告。不会跨区发送密钥或在认证失败后自动改用网页登录。

沿用网页通道时运行 `authenticate.ps1`，在本机输入邮箱、密码和必要的 MFA。已有网页凭据保留，可设置 `GARMIN_CN_SYNC_PROVIDER=web` 切回。不要把密钥、密码、验证码、Cookie 或 token 发到聊天、Issue 或日志中。配置与同步均针对自己的中国区账户；一个数据库只对应一个账户。

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
| `GARMIN_CN_SYNC_PROVIDER` | `auto`（默认：有 Key 用官方）、`personal`（强制官方）或 `web`（原网页通道）。修改后重启 MCP 服务。 |

MCP 服务器与缓存运行在本机；凭据不会放入聊天。用户请求的数据会由 MCP 工具返回给调用客户端，以完成该次查询或分析，因此也请检查客户端自身的数据处理设置。

### 限制与责任

- 官方通道固定连接 `personal.connectapi.garmin.cn`，原有 `garminconnect` 网页通道可选。历史缓存可能包含两种来源；本社区插件独立维护，接口能力与可用性由 Garmin 决定。
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

Garmin China Sync is a locally running MCP plugin that syncs Garmin China (`garmin.cn`) daily health data and activities to a local SQLite cache for on-demand queries from Codex or another compatible MCP client. Version `0.2.0` targets Windows 10/11.

The plugin supports the official **Personal API** and the existing unofficial China web provider. It reads Garmin health and activity data and updates the local cache. In default `auto` mode, a saved Personal API key selects the official provider; otherwise the web provider is used. China-region authentication, sleep, HRV, Body Battery and activities were verified on 2026-10-26.

### Features

- **Daily health, sleep, and recovery data:** Reads daily stats, sleep, HRV, and Body Battery responses. Compact daily results include steps, resting heart rate (falling back to minimum heart rate when that field is absent), average stress, sleep duration and score, last-night average HRV, Body Battery response, per-day errors, and sync time. Raw cached responses can be requested with `include_raw=true`.
- **Official batch sync:** Uses four date-range requests for daily summaries, sleep summaries, HRV summaries and Body Battery. Official v2 daily fields are retained alongside compatibility aliases. Official cached sleep and HRV data are summaries; per-point curves are not additionally fetched.
- **Activity history:** Syncs and queries activities by date range. Initial bootstrap requests up to 365 days; regular sync defaults to the latest 7 days. Full activity responses are cached locally.
- **Metric coverage:** Official activity responses include training load/effect, distance, duration and heart rate. The activity list and detail endpoints did not return legacy VO2max in live verification. Previously cached VO2max for the same activity is retained with `_retained_field_sources`; a new activity's missing value is left missing.
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
pwsh -NoLogo -NoProfile -File .\scripts\authenticate-personal.ps1
pwsh -NoLogo -NoProfile -NonInteractive -File .\scripts\bootstrap.ps1
```

`setup.ps1` creates `.venv` and installs dependencies. Create your key on the [China Personal API page](https://connect.garmin.cn/app/settings/personalApiToken), then enter it at `authenticate-personal.ps1`'s local hidden prompt. The key is stored under `GarminCnSync / personal-api-key-cn` in Windows Credential Manager; chunked bearer tokens use the separate `GarminCnSync.PersonalApi.CN` service and are refreshed near expiry. A 401 triggers one refresh/retry; other errors are reported without automatically changing provider or region.

For the legacy web provider, run `authenticate.ps1` and enter the email, password and MFA code locally. Existing web credentials are preserved; set `GARMIN_CN_SYNC_PROVIDER=web` to use them. Never place keys, passwords, MFA codes, cookies or tokens in chat, issues or logs. Use one database per China-region account.

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
| `GARMIN_CN_SYNC_PROVIDER` | `auto` (default: official when a key is saved), `personal` (force official), or `web` (legacy). Restart the MCP server after changing it. |

The MCP server and cache run locally, and credentials are not placed in chat. Data requested through an MCP tool is returned to the calling client for that query or analysis; review that client's own data-handling settings as well.

### Limitations and responsibility

- The official provider uses `personal.connectapi.garmin.cn`; the existing `garminconnect` web provider remains selectable. Historical cache may contain both sources. This independently maintained community plugin depends on Garmin's API capabilities and availability.
- Use only with an account you are authorized to access, and review applicable Garmin terms and local requirements.
- The plugin reads from Garmin and does not change account settings or activity data; local sync/import writes to the SQLite cache.
- Health and fitness information is for personal data organization only, not a medical device, diagnosis, or treatment advice.

### Development and tests

Run from the plugin directory:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use synthetic data and never log in to a real Garmin account or run a live sync automatically.
