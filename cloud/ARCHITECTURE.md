# Cloud Edition — source audit and architecture

## P0 source audit

The existing Desktop Edition uses `PersonalApiClient` for Garmin CN token exchange and read-only requests, a local FastMCP stdio server in `server.py`, local SQLite/cache operations in `service.py` and `database.py`, and Windows Credential Manager through `secrets.py`. Its manifest points to a PowerShell-launched local process. Those local process, key-vault, and SQLite dependencies explain its desktop-only behavior.

The Cloud Edition keeps that implementation unchanged and adds a separate stateless Worker. It reuses the exact tested Garmin CN host, Personal API token endpoint, date-summary endpoints, and activity-list endpoint already present in `personal_api.py`. The activity record endpoint is fixed to `/activity-service/activity/{numericId}`, matching Garmin's published Personal API client implementation. Endpoint shapes and live account access still require post-deploy verification from the Worker environment.

## Request flow

1. ChatGPT discovers the protected resource and authorization server from the Worker.
2. The Cloudflare OAuth Provider handles OAuth 2.1 authorization code + PKCE, token issuance/refresh/revocation, client registration, state, and request validation.
3. The Worker authorization page identifies the client and redirect host. The user enters their China Personal API Key in a password field and accepts read-only access.
4. The Worker makes a single token-exchange request to Garmin China to verify the key. It discards the returned bearer token. It never puts the key in a URL, OAuth state, or an MCP response.
5. On successful verification and consent, the provider stores the API Key as encrypted OAuth `props`. OAuth tokens, grants and short-lived protocol state use `OAUTH_KV`; no health or activity data is persisted there.
6. For an authenticated tool call, the provider validates the access token, audience, expiry and scope. The MCP handler reads only that grant's encrypted properties, exchanges the Garmin key for a short-lived Garmin bearer token, calls one hard-coded API path, and returns the response.

OAuth grants have a 1-hour access token and 30-day refresh token lifetime. Users can disconnect the ChatGPT connector/revoke the OAuth grant and can delete the Garmin Personal API Key in Garmin Connect. Deleting the Garmin key also invalidates Garmin tokens associated with it.

## Security controls implemented

- `createMcpHandler()` stateless MCP server; no Durable Object, SQL, or activity cache.
- `@cloudflare/workers-oauth-provider` rather than a handwritten authorization-code implementation.
- Cloudflare provider supplies OAuth PKCE, callback validation, audience/scope/expiry checks, code replay protections, revocation and encrypted props.
- Garmin Key accepted only by a same-origin HTTPS form POST. Consent uses the provider's browser-bound one-time handle. HTML uses no-store, no-referrer and a restrictive Content Security Policy.
- Key is tested before provider persistence. No credential is included in log statements, response payloads, query strings, or error details.
- Garmin host is fixed; paths are hard-coded; redirects are disabled; upstream request timeout is bounded.
- Read-only tools validate date windows, record limits and numeric activity identifiers.
- Remote worker only uses its own `OAUTH_KV` namespace for OAuth protocol data; no Garmin response persistence.

## Verification status

- Source audit: completed locally.
- Native Node unit checks: 5 passed (date validation, key-to-token request, URL allowlisting, activity detail ID restriction, daily merging, and upstream error redaction are covered across those checks).
- TypeScript compile / Wrangler workerd tests: pending; npm registry access from this execution environment failed and no packages were available locally.
- Worker outbound access to `personal.connectapi.garmin.cn`: not yet verified; this must be tested after deployment.
- Live OAuth PKCE, callback replay, revocation and tenant isolation: code uses Cloudflare's OAuth Provider implementation, but end-to-end behavior is not verified until dependencies and a deployed Worker are available.
- ChatGPT web/mobile connection: not yet verified.

## Known deployment prerequisite

The deployer needs a Cloudflare account, a KV namespace ID, and Wrangler authorization. Those credentials are not present in the current local environment. Deploying the Worker will create a serverless remote endpoint in the user's Cloudflare account; it is not a desktop process and does not require a VPS.
