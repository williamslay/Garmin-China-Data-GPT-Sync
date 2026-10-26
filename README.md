# Garmin China Sync

[简体中文](#简体中文) · [English](#english)

## 简体中文

Garmin China Sync 为 Garmin 中国区 Personal API 提供只读 MCP 工具。**主分支采用 Cloud Edition**：每位使用者把 Cloudflare Worker 和 OAuth 凭据存储部署在自己的账户中，再把自己的 MCP 地址连接到 Codex 或兼容客户端。仓库维护者不托管共享 Garmin 服务。

工具读取每日摘要、睡眠、HRV、Body Battery、活动列表和单次活动详情。健康与活动记录按请求实时读取，不写入 Worker 数据库；Garmin Key 经 HTTPS 授权页提交，并由 Cloudflare OAuth Provider 加密保存。

桌面版 SQLite 插件保留在 `codex/desktop-edition` 分支。

### 从 GitHub 仓库市场安装指导插件

此市场插件提供部署与数据解读技能。由于每个人部署出的 Worker URL 都不同，安装市场插件后还要单独添加自己的远程 MCP 连接。

~~~powershell
codex plugin marketplace add williamslay/Garmin-China-Data-GPT-Sync --ref main
~~~

在 Codex 桌面端打开 Plugins Directory，从 `Garmin China Sync` 市场安装 `Garmin China Sync Cloud`。然后按照插件的 Setup 指引部署自己的 Worker，并在客户端添加 OAuth MCP 地址：`https://<自己的-worker>.<账户>.workers.dev/mcp`。

### 部署自己的 Cloud Worker

需要 Node.js 24+、pnpm、Cloudflare Workers/KV 账户和 Garmin 中国区 Personal API Key。详情见[Cloud Edition 指南](cloud/README.md)。

1. 在 `cloud/worker` 安装依赖并登录 Wrangler。
2. 创建 `OAUTH_KV` 命名空间，把 ID 写入 `cloud/worker/wrangler.jsonc`。
3. 部署 Worker，复制 Wrangler 输出的 HTTPS 地址。
4. 在 Codex/ChatGPT 添加远程 MCP 服务器，地址以 `/mcp` 结尾，认证选择 OAuth。
5. 在 Garmin 授权页输入 Personal API Key；不要把 Key 放进对话或配置文件。

工具范围和隐私边界见 [cloud/README.md](cloud/README.md)、[隐私说明](cloud/PRIVACY.md) 和 [使用条款](cloud/TERMS.md)。本项目是独立社区软件，不是 Garmin 官方产品，不提供医疗诊断。

## English

Garmin China Sync provides read-only MCP tools for the Garmin China Personal API. **The main branch is the Cloud Edition**: each user deploys the Cloudflare Worker and OAuth credential store in their own account, then connects that personal MCP URL to Codex or a compatible client. The repository maintainer does not host a shared Garmin service.

Tools read daily summaries, sleep, HRV, Body Battery, activity lists, and individual activity details. Health and activity records are fetched on demand and are not written to a Worker database. The Garmin Key is submitted through HTTPS authorization and encrypted by Cloudflare's OAuth provider.

The SQLite Desktop Edition remains on the `codex/desktop-edition` branch.

### Install the GitHub marketplace guide plugin

The marketplace plugin provides setup and data-interpretation skills. Since each user deploys a different Worker URL, you must add your own remote MCP connection separately after installing the plugin.

~~~powershell
codex plugin marketplace add williamslay/Garmin-China-Data-GPT-Sync --ref main
~~~

In the Codex desktop app, open the Plugins Directory and install `Garmin China Sync Cloud` from the `Garmin China Sync` marketplace. Follow its Setup instructions to deploy your Worker, then add your personal OAuth MCP endpoint: `https://<your-worker>.<account>.workers.dev/mcp`.

### Deploy your own Cloud Worker

Requirements: Node.js 24+, pnpm, a Cloudflare Workers/KV account, and a Garmin China Personal API Key. See the [Cloud Edition guide](cloud/README.md).

1. Install dependencies in `cloud/worker` and authenticate Wrangler.
2. Create the `OAUTH_KV` namespace and put its ID in `cloud/worker/wrangler.jsonc`.
3. Deploy the Worker and copy its HTTPS URL from Wrangler.
4. Add a remote MCP server in Codex/ChatGPT, using the URL ending in `/mcp` and OAuth authentication.
5. Enter the Personal API Key on Garmin's authorization page; never place it in chat or a config file.

See [cloud/README.md](cloud/README.md), the [privacy notice](cloud/PRIVACY.md), and [terms](cloud/TERMS.md) for tool boundaries and data handling. This is independent community software, not an official Garmin product, and does not provide medical diagnoses.
