# Garmin China Sync — Cloud Edition

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/williamslay/Garmin-China-Data-GPT-Sync/tree/main/cloud/worker)

Cloud Edition runs as a remote MCP endpoint on Cloudflare Workers. Deploy one Worker to your own Cloudflare account, then connect that HTTPS endpoint to ChatGPT. There is no desktop process or user-managed VPS. Garmin data remains at Garmin until a tool call; the Worker fetches it live and returns the requested result to ChatGPT.

This edition is separate from the existing Desktop Edition. The Worker does not sync history into a database or cache Garmin health/activity responses. Cloudflare KV is used only by Cloudflare's OAuth provider for OAuth clients, short-lived authorization state/codes, tokens, and encrypted per-user credential properties. The Garmin Key is entered in a browser form during OAuth, verified with Garmin, and stored only inside those encrypted OAuth properties. The default OAuth grant expires after 30 days; disconnect in ChatGPT or revoke/delete the Personal API Key in Garmin Connect to stop future access.

## Tools

| Tool | Reads | Boundaries |
| --- | --- | --- |
| `garmin_get_daily` | Daily summary, sleep, HRV, Body Battery | 1–31 calendar days |
| `garmin_get_activities` | Activity list | 1–366 calendar days, up to 100 records |
| `garmin_get_activity_detail` | One activity summary/detail by ID | Positive numeric activity ID |

All calls use `personal.connectapi.garmin.cn`. The Worker exposes read-only tools and does not accept caller-provided URLs or endpoint paths. It exchanges the Personal API Key for a Garmin bearer token when a tool runs and does not retain the bearer token. API errors omit response bodies and credential values.

## One-click deployment

You need a GitHub or GitLab account, a Cloudflare account, and a Garmin China Personal API Key. Select **Deploy to Cloudflare** above. Sign in to Cloudflare and authorize access to your GitHub/GitLab account when prompted. Cloudflare copies the isolated `cloud/worker` application into a repository in your account, automatically creates and binds its `OAUTH_KV` namespace, builds the Worker, and deploys it. You do not need to install Node.js/pnpm or edit a Wrangler file.

Cloudflare gives you a Worker URL such as `https://<worker>.<account>.workers.dev`. In ChatGPT or Codex, add a remote MCP server at `https://<worker>.<account>.workers.dev/mcp` and choose OAuth. On first connection, enter the Garmin China Personal API Key on the HTTPS authorization page. Never put the Garmin key in chat, GitHub, or a configuration file.

Cloudflare creates a separate copy of the Worker source in your GitHub/GitLab account. Changes to this repository do not automatically update that copy. The button and deployment have no separate charge. Cloudflare Free currently includes 100,000 Worker requests per day; 100,000 KV reads and 1,000 writes, deletes, and list operations per day; 1 GB KV storage; and 3,000 Workers Builds minutes per month. Personal use will usually fit within the free quotas. Paid plans or paid products can incur charges; see [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) and [Workers Builds limits](https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/) for current details.

## Manual deployment

Use this path if you do not have GitHub/GitLab or prefer to deploy from your computer. Requirements: Node.js 24+, pnpm, and a Cloudflare account with Workers access. Wrangler creates the KV namespace from the binding in `wrangler.jsonc` during deployment.

```powershell
cd cloud/worker
pnpm install
pnpm exec wrangler login
pnpm exec wrangler deploy
```

Wrangler reports your Worker HTTPS host (normally `<worker>.<account>.workers.dev`). Continue with the remote MCP and OAuth connection steps above.

For an MCP client that imports a manifest, run `scripts/package.ps1 -McpUrl https://<worker>.<account>.workers.dev/mcp` to generate a URL-specific Cloud plugin folder and ZIP. The generated manifest cannot work until the Worker has been deployed and its real URL supplied.

## GitHub repository marketplace

The main-branch Codex marketplace plugin is a setup and interpretation guide. It deliberately does not point at the repository maintainer's Worker: each user deploys a different endpoint. After installing the GitHub marketplace plugin, deploy your own Worker using the steps above, then add your own `https://<worker>.<account>.workers.dev/mcp` URL as a remote OAuth MCP server in the client. The Garmin tools become available after that separate connection is authorized.

From Codex CLI, add the GitHub marketplace with:

```powershell
codex plugin marketplace add williamslay/Garmin-China-Data-GPT-Sync --ref main
```

In the Codex desktop app, choose `Garmin China Sync` in the Plugins Directory and install `Garmin China Sync Cloud`. Its Setup skill points to this guide. The SQLite Desktop Edition remains available on the `codex/desktop-edition` Git branch.

## Local checks

The dependency-free Garmin request and validation checks run with the bundled Node runtime:

```powershell
node --experimental-strip-types --test cloud/worker/test/garmin.test.mjs
```

`pnpm test` runs the same tests. `pnpm typecheck` and Wrangler local runtime tests require npm dependencies. A live deployment and ChatGPT web/mobile connection require an authenticated Cloudflare account and a deployed Worker URL.

## Privacy and service boundaries

- The user deploys and controls their own Cloudflare Worker account. This repository maintainer does not operate a shared API endpoint.
- The user supplies their own Garmin Personal API Key through the HTTPS OAuth authorization page.
- Cloudflare's OAuth Provider stores grants and encrypted per-user props in the `OAUTH_KV` namespace. OAuth state is temporary; grant data expires or can be revoked. See [Cloudflare OAuth Provider storage](https://github.com/cloudflare/workers-oauth-provider/blob/main/storage-schema.md).
- Garmin health and activity response bodies are not stored in KV or another Worker database by this project. Each MCP result is returned to ChatGPT so it can answer the user's request.
- ChatGPT receives the data returned by the user's tools and processes it under the user's ChatGPT settings and applicable terms.
- Garmin's Personal API is intended for individuals to access their own Garmin data. Deploying a separate Worker for your own use aligns with that model; this project does not provide a maintainer-hosted multi-user Garmin service.
- The project is independent community software, not an official Garmin product. Review Garmin's current terms and revoke the key in Garmin Connect when access is no longer wanted.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the audit record and [PRIVACY.md](PRIVACY.md) for a concise privacy notice.

## 简体中文

云端版运行在 Cloudflare Workers 上的远程 MCP 服务中。你把 Worker 部署到自己的 Cloudflare 账户，再将 HTTPS 地址连接到 ChatGPT；无需桌面程序，也无需维护 VPS。Garmin 数据平时保存在 Garmin；调用工具时，Worker 实时读取所选记录并返回给 ChatGPT。

云端版与原桌面版分开。Worker 不把 Garmin 活动或健康响应同步到数据库，也不缓存这些数据。Cloudflare KV 只供官方 OAuth Provider 保存 OAuth 客户端、短期授权状态/代码、令牌以及加密的每用户凭据。用户在 OAuth 浏览器页面输入 Garmin 中国区 Personal API Key，Worker 先向 Garmin 验证，通过后才将 Key 放入加密的 OAuth 凭据属性。默认授权记录最长 30 天，可在 ChatGPT 断开连接或在 Garmin Connect 删除 Key。

### 工具

| 工具 | 读取内容 | 限制 |
| --- | --- | --- |
| `garmin_get_daily` | 每日摘要、睡眠、HRV、Body Battery | 1–31 天 |
| `garmin_get_activities` | 活动列表 | 1–366 天，最多 100 条 |
| `garmin_get_activity_detail` | 按 ID 读取一次活动摘要/详情对象 | 正整数活动 ID |

请求固定使用 `personal.connectapi.garmin.cn`。工具只读，不接受调用方传入 URL 或 API 路径。每次工具调用时，Worker 用 Personal API Key 换取 Garmin 短时令牌，不保存该令牌。接口错误不会包含响应正文或凭据。

### 一键部署

需要 GitHub 或 GitLab 账号、Cloudflare 账号和 Garmin 中国区 Personal API Key。点击本页顶部的 **Deploy to Cloudflare**，登录 Cloudflare，并按提示授权连接 GitHub/GitLab。Cloudflare 会把独立的 `cloud/worker` 项目复制到你自己的代码仓库，自动创建并绑定 `OAUTH_KV`，然后构建和部署。无需在本机安装 Node.js/pnpm，也无需编辑 Wrangler 配置。

部署完成后，Cloudflare 会显示 Worker 地址，例如 `https://<worker>.<account>.workers.dev`。在 ChatGPT 或 Codex 添加远程 MCP 服务器，地址末尾加 `/mcp`，认证选择 OAuth。首次连接时，在 HTTPS 授权页输入 Garmin 中国区 Personal API Key。不要把 Garmin Key 放进对话、GitHub 仓库或配置文件。

Cloudflare 会在你的 GitHub/GitLab 账号下创建一份 Worker 代码副本；本仓库后续更新不会自动同步到那份副本。按钮和部署本身不单独收费。按 Cloudflare 当前 Free 额度，Workers 每日含 100,000 次请求；KV 每日含 100,000 次读取、各 1,000 次写入/删除/列举，存储 1 GB；Workers Builds 每月含 3,000 分钟。个人使用通常可留在免费额度内。若主动开通付费计划或使用收费资源，可能产生费用；额度会调整，查看 [Workers 价格](https://developers.cloudflare.com/workers/platform/pricing/) 和 [Builds 限额](https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/)。

### 手动部署

没有 GitHub/GitLab 账号或希望从本机部署时，需要 Node.js 24+、pnpm 和 Cloudflare Workers 账户。在 PowerShell 7 中：

```powershell
Set-Location cloud/worker
pnpm install
pnpm exec wrangler login
pnpm exec wrangler deploy
```

Wrangler 会按 `wrangler.jsonc` 中的绑定自动创建并关联 KV，然后显示 Worker 的 HTTPS 地址。接着按上文说明，在 ChatGPT 或 Codex 添加远程 MCP 地址并使用 OAuth 连接。

如果客户端支持导入插件清单，可运行 `scripts/package.ps1 -McpUrl https://<worker>.<account>.workers.dev/mcp` 生成绑定此 URL 的 Cloud 插件目录与 ZIP。必须先部署 Worker 并使用实际地址，生成的清单才可连接。

### 数据与服务边界

- 每位使用者把 Worker 部署在自己的 Cloudflare 账户中；仓库维护者不运行共享数据服务。
- Garmin Key 只在 HTTPS OAuth 授权页录入。
- Cloudflare OAuth Provider 将授权记录和加密后的每用户属性写入部署者的 `OAUTH_KV`。不会将 Garmin 活动、睡眠或健康响应写入 KV 或 Worker 数据库。
- 工具返回的数据会发送给 ChatGPT，用于用户本次请求的分析；ChatGPT 按用户自己的设置和适用条款处理这些结果。
- Garmin Personal API 面向个人访问自己的 Garmin 数据。本项目提供个人自行部署方式，不提供由维护者统一托管、供多用户共用的 Garmin 服务。
- 本项目为独立社区软件，不是 Garmin 官方产品。请查阅 Garmin 当前条款；不再需要连接时，可在 Garmin Connect 删除 Personal API Key。

部署前请阅读[隐私说明](PRIVACY.md)和[使用条款](TERMS.md)。
