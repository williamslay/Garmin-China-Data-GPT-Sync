[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/williamslay/Garmin-China-Data-GPT-Sync/tree/main/cloud/worker)

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

### 最简单的部署方式

需要 GitHub（或 GitLab）账号、Cloudflare 账号和 Garmin 中国区 Personal API Key。点击页面顶部的 **Deploy to Cloudflare** 按钮，授权 Cloudflare 读取代码仓库并部署。Cloudflare 会把 `cloud/worker` 复制到你自己的仓库、自动创建并绑定 KV，然后部署 Worker。无需安装 Node.js/pnpm、手动创建 KV 或编辑配置文件。

部署完成后，复制 Cloudflare 显示的 Worker 地址，在 Codex/ChatGPT 添加远程 MCP 服务器：地址末尾加 `/mcp`，认证选择 OAuth。授权页面只输入 Garmin Personal API Key。不要把 Key 放进对话或配置文件。

按钮和部署本身不单独收费。按 Cloudflare 当前 Free 额度，Workers 每日含 100,000 次请求；KV 每日含 100,000 次读取、各 1,000 次写入/删除/列举，存储 1 GB；Workers Builds 每月含 3,000 分钟。个人使用通常可留在免费额度内。若主动开通付费计划或使用收费资源，可能产生费用；额度会调整，查看 [Workers 价格](https://developers.cloudflare.com/workers/platform/pricing/) 和 [Builds 限额](https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/)。

没有 GitHub/GitLab 账号时，可按[手动部署指南](cloud/README.md#手动部署)用 Node.js 和 pnpm 部署。

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

### Simplest deployment path

You need a GitHub or GitLab account, a Cloudflare account, and a Garmin China Personal API Key. Select **Deploy to Cloudflare** at the top of this README, authorize Cloudflare to access the source repository, and deploy. Cloudflare copies `cloud/worker` to a repository under your account, creates and binds the KV namespace, and deploys the Worker. No local Node.js/pnpm setup or Wrangler commands are required.

After deployment, copy the Worker URL Cloudflare shows. Add a remote MCP server in Codex/ChatGPT with `/mcp` at the end of the URL and OAuth authentication. Enter the Garmin Personal API Key only on the HTTPS authorization page, never in chat or a config file.

The button and deployment have no separate charge. Cloudflare Free currently includes 100,000 Worker requests per day; 100,000 KV reads and 1,000 writes, deletes, and list operations per day; 1 GB KV storage; and 3,000 Workers Builds minutes per month. Personal use will usually fit within the free quotas. Paid plans or paid products can incur charges; check [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) and [Builds limits](https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/) for current terms.

Users without GitHub/GitLab can follow the [manual deployment guide](cloud/README.md#manual-deployment) using Node.js and pnpm.

See [cloud/README.md](cloud/README.md), the [privacy notice](cloud/PRIVACY.md), and [terms](cloud/TERMS.md) for tool boundaries and data handling. This is independent community software, not an official Garmin product, and does not provide medical diagnoses.
