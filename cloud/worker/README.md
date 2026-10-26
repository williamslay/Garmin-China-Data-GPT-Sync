[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/williamslay/Garmin-China-Data-GPT-Sync/tree/main/cloud/worker)

<!-- dash-content-start -->

# Garmin China Sync Cloud Worker

Deploy your own read-only Garmin China MCP server to Cloudflare. The Deploy to Cloudflare button copies this self-contained Worker project to your GitHub/GitLab account, automatically provisions its KV namespace, and deploys it.

You need a GitHub or GitLab account, a Cloudflare account, and a Garmin China Personal API Key. After deployment, add the shown Worker URL to ChatGPT or Codex as a remote MCP server ending in `/mcp`, with OAuth authentication. Enter the Garmin Key only on the HTTPS authorization page.

The button and deployment have no separate charge. Cloudflare Free currently includes 100,000 Worker requests per day; 100,000 KV reads and 1,000 writes, deletes, and list operations per day; 1 GB KV storage; and 3,000 Workers Builds minutes per month. Personal use will usually fit within the free quotas. Paid plans or paid products can incur charges; see [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) and [Workers Builds limits](https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/) for current details.

See the [full setup guide](../README.md) for the manual alternative, tools, data handling, and privacy details.

<!-- dash-content-end -->
