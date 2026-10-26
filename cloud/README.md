# Garmin China Sync — Cloud Edition

Cloud Edition runs as a remote MCP endpoint on Cloudflare Workers. Deploy one Worker to your own Cloudflare account, then connect that HTTPS endpoint to ChatGPT. There is no desktop process or user-managed VPS. Garmin data remains at Garmin until a tool call; the Worker fetches it live and returns the requested result to ChatGPT.

This edition is separate from the existing Desktop Edition. The Worker does not sync history into a database or cache Garmin health/activity responses. Cloudflare KV is used only by Cloudflare's OAuth provider for OAuth clients, short-lived authorization state/codes, tokens, and encrypted per-user credential properties. The Garmin Key is entered in a browser form during OAuth, verified with Garmin, and stored only inside those encrypted OAuth properties. The default OAuth grant expires after 30 days; disconnect in ChatGPT or revoke/delete the Personal API Key in Garmin Connect to stop future access.

## Tools

| Tool | Reads | Boundaries |
| --- | --- | --- |
| `garmin_get_daily` | Daily summary, sleep, HRV, Body Battery | 1–31 calendar days |
| `garmin_get_activities` | Activity list | 1–366 calendar days, up to 100 records |
| `garmin_get_activity_detail` | One activity summary/detail by ID | Positive numeric activity ID |

All calls use `personal.connectapi.garmin.cn`. The Worker exposes read-only tools and does not accept caller-provided URLs or endpoint paths. It exchanges the Personal API Key for a Garmin bearer token when a tool runs and does not retain the bearer token. API errors omit response bodies and credential values.

## Deploy your own endpoint

Requirements: Node.js 24+, pnpm, a Cloudflare account with Workers and KV access, and a Garmin China Personal API Key. Cloud Edition has no serverless database service to maintain, but it does require a remote Worker endpoint in your Cloudflare account.

From PowerShell 7:

```powershell
cd cloud/worker
pnpm install
pnpm exec wrangler login
pnpm exec wrangler kv namespace create OAUTH_KV
```

Copy the returned namespace ID into `cloud/worker/wrangler.jsonc` at `kv_namespaces[0].id`, then run:

```powershell
pnpm test
pnpm typecheck
pnpm exec wrangler deploy
```

Wrangler reports your Worker HTTPS host (normally `<worker>.<account>.workers.dev`). The Worker derives the OAuth issuer and protected-resource audience from that actual host. In ChatGPT, add a remote MCP connector using `https://<worker>.<account>.workers.dev/mcp`, choose OAuth, and connect. On first authorization, enter the Garmin China Personal API Key on the consent page. Never paste the Garmin key into the conversation or a plugin configuration file.

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

### 部署自己的服务

需要 Node.js 24+、pnpm、可使用 Workers 与 KV 的 Cloudflare 账户，以及 Garmin 中国区 Personal API Key。在 PowerShell 7 中：

```powershell
Set-Location cloud/worker
pnpm install
pnpm exec wrangler login
pnpm exec wrangler kv namespace create OAUTH_KV
```

将命令返回的 namespace ID 填入 `cloud/worker/wrangler.jsonc` 的 `kv_namespaces[0].id`，然后执行：

```powershell
pnpm test
pnpm typecheck
pnpm exec wrangler deploy
```

Wrangler 会显示 Worker 的 HTTPS 地址（通常为 `<worker>.<account>.workers.dev`）。Worker 会根据实际访问域名生成 OAuth issuer 与资源受众地址。到 ChatGPT 添加远程 MCP 连接，地址填 `https://<worker>.<account>.workers.dev/mcp`，选择 OAuth 并连接。首次授权时，在浏览器授权页输入 Garmin 中国区 Personal API Key。不要把 Garmin Key 发到对话，也不要放进插件配置文件。

如果客户端支持导入插件清单，可运行 `scripts/package.ps1 -McpUrl https://<worker>.<account>.workers.dev/mcp` 生成绑定此 URL 的 Cloud 插件目录与 ZIP。必须先部署 Worker 并使用实际地址，生成的清单才可连接。

### 数据与服务边界

- 每位使用者把 Worker 部署在自己的 Cloudflare 账户中；仓库维护者不运行共享数据服务。
- Garmin Key 只在 HTTPS OAuth 授权页录入。
- Cloudflare OAuth Provider 将授权记录和加密后的每用户属性写入部署者的 `OAUTH_KV`。不会将 Garmin 活动、睡眠或健康响应写入 KV 或 Worker 数据库。
- 工具返回的数据会发送给 ChatGPT，用于用户本次请求的分析；ChatGPT 按用户自己的设置和适用条款处理这些结果。
- Garmin Personal API 面向个人访问自己的 Garmin 数据。本项目提供个人自行部署方式，不提供由维护者统一托管、供多用户共用的 Garmin 服务。
- 本项目为独立社区软件，不是 Garmin 官方产品。请查阅 Garmin 当前条款；不再需要连接时，可在 Garmin Connect 删除 Personal API Key。

部署前请阅读[隐私说明](PRIVACY.md)和[使用条款](TERMS.md)。
