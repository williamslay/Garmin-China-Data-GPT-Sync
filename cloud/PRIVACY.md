# Privacy notice — Garmin China Sync Cloud Edition

Cloud Edition is community software deployed by each user to their own Cloudflare account. The repository maintainer does not run a shared endpoint.

## Data used

When a user connects the MCP server, they enter a Garmin China Personal API Key on the Worker authorization page. The Worker sends that key to Garmin's Personal API token endpoint to verify it. On successful verification and consent, Cloudflare's OAuth Provider stores the key in encrypted OAuth grant properties in the deployer's `OAUTH_KV` namespace. OAuth protocol state, clients, authorization codes, access tokens, and grants are also stored there according to the provider's storage design.

When the user invokes a tool, the Worker exchanges the stored key for a short-lived Garmin access token, requests the selected daily health or activity endpoint, and returns the result to ChatGPT. The Worker does not save Garmin health or activity responses in KV, a SQL database, object storage, or an analytics database.

## Retention and control

OAuth access tokens expire after one hour. Refresh grants expire after 30 days unless renewed, and a user may disconnect/revoke the connector at any time. A user can also delete their Personal API Key in Garmin Connect; Garmin states that deleting a key invalidates associated access tokens. The deployer controls Cloudflare account access and can delete the Worker and its KV namespace to remove OAuth records.

## Third parties

Garmin receives the Personal API Key only at its fixed China-region token endpoint and receives bearer tokens with read requests. ChatGPT receives tool results for the user's requested analysis. Cloudflare hosts and executes the Worker and stores OAuth protocol records for the deployer. Review Garmin, Cloudflare, and ChatGPT policies and account settings before connecting sensitive health data.

## Scope and contact

The tools are read-only. They do not update Garmin settings or activities. This notice describes this repository's Cloud Edition behavior; each deployer should review it against their own Worker configuration before use. Report code or privacy issues through the repository's GitHub issue tracker.

---

# 简体中文

云端版由使用者自行部署到自己的 Cloudflare 账户；仓库维护者不提供共享服务。

## 使用的数据

连接 MCP 服务时，用户在 Worker 的授权页面输入 Garmin 中国区 Personal API Key。Worker 会将 Key 发给 Garmin Personal API 令牌接口进行验证。验证通过并经用户同意后，Cloudflare OAuth Provider 会把 Key 加密保存在部署者的 `OAUTH_KV` 授权属性中。OAuth 状态、客户端、授权代码、访问令牌和授权记录也按 Provider 的存储方案保存在该 KV 命名空间。

用户调用工具时，Worker 用已保存的 Key 换取短时 Garmin 访问令牌，查询所选日期或活动，再把结果返回给 ChatGPT。项目不会把 Garmin 健康或活动响应保存到 KV、SQL 数据库、对象存储或分析数据库。

## 保留与控制

OAuth 访问令牌一小时后过期；刷新授权记录默认 30 天后到期，成功续期时会更新授权记录。用户可断开 ChatGPT 连接或撤销 OAuth 授权，也可在 Garmin Connect 删除 Personal API Key。Garmin 说明，删除 Key 会使相关访问令牌失效。部署者可以删除 Worker 与 KV 命名空间，以清除 OAuth 记录。

## 第三方服务

Garmin 只会在固定的中国区令牌接口收到 Personal API Key，并在数据读取请求中收到 bearer token。ChatGPT 会收到用户请求工具返回的数据。Cloudflare 托管并运行 Worker，也会按部署者配置存储 OAuth 协议记录。连接健康数据前，请查阅 Garmin、Cloudflare 与 ChatGPT 的政策及账户设置。

## 范围与联系

工具只读，不会更改 Garmin 账户设置或活动。本说明针对本仓库云端版；每位部署者应在启用前按自己的 Worker 配置再次核对。代码或隐私问题可通过仓库 GitHub Issues 反馈。
