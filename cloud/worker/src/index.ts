import { createMcpHandler, getMcpAuthContext } from "agents/mcp/server";
import { McpServer } from "@modelcontextprotocol/server";
import { AuthorizationError, OAuthProvider, type OAuthHelpers } from "@cloudflare/workers-oauth-provider";
import { z } from "zod";
import { exchangeKeyForToken, getActivities, getActivityDetail, getDaily } from "./garmin";

interface Env {
  OAUTH_KV: KVNamespace;
  OAUTH_PROVIDER: OAuthHelpers;
}

interface GarminProps {
  garminApiKey: string;
  userId: string;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);
}

function html(body: string, status = 200): Response {
  return new Response(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Garmin China Sync</title></head><body>${body}</body></html>`, {
    status,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      "Referrer-Policy": "no-referrer",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    },
  });
}

function authorizationPage(clientName: string, clientDomain: string | undefined, redirectHost: string, handle: string, scope: string[], nonce: string, error = ""): string {
  const safeName = escapeHtml(clientName);
  const clientIdentity = clientDomain ? `Published by <strong>${escapeHtml(clientDomain)}</strong>.` : "This client name is self-asserted and its domain is unverified.";
  const safeHost = escapeHtml(redirectHost);
  const scopeInputs = scope.map((value) => `<input type="hidden" name="scope" value="${escapeHtml(value)}">`).join("");
  const safeError = error ? `<p role="alert" style="color:#a00">${escapeHtml(error)}</p>` : "";
  return `<main style="max-width:40rem;margin:3rem auto;padding:0 1rem;font:16px/1.6 system-ui,sans-serif;color:#17202a"><h1>连接 Garmin 中国区</h1><p><strong>${safeName}</strong> 请求读取你的 Garmin 数据。${clientIdentity}授权回调目标：<code>${safeHost}</code>。</p><p>授权范围：只读活动列表与单次活动摘要、每日统计、睡眠、HRV 和 Body Battery。</p><p>授权后，服务器会将 Garmin Personal API Key 加密保存在 OAuth 凭据存储中，用它实时读取 Garmin 数据。运动和健康记录不会写入数据库。</p>${safeError}<form id="consent-form" method="post" autocomplete="off"><input type="hidden" name="handle" value="${escapeHtml(handle)}"><input type="hidden" id="decision-field" name="decision" value="approve">${scopeInputs}<label for="garmin-key">Garmin China Personal API Key</label><br><input id="garmin-key" name="garmin_key" type="password" required autocomplete="new-password" spellcheck="false" style="box-sizing:border-box;width:100%;padding:.75rem;margin:.5rem 0 1rem"><p><label><input type="checkbox" name="consent" value="yes" required> 我同意该 MCP 服务代表我只读访问 Garmin 数据，并理解 Key 会加密保存在服务授权记录中。</label></p><button id="approve-button" data-decision="approve" type="submit">验证 Key 并授权</button> <button data-decision="deny" type="submit" formnovalidate>拒绝</button><p id="submit-status" role="status" aria-live="polite"></p></form><p><small>可随时在 Garmin Connect 撤销 Personal API Key。不要把 Key 发到聊天或任何其他地方。</small></p><script nonce="${escapeHtml(nonce)}">const form=document.getElementById('consent-form');const decision=document.getElementById('decision-field');let submitted=false;form.addEventListener('submit',event=>{if(submitted){event.preventDefault();return}submitted=true;const button=event.submitter;decision.value=button&&button.dataset.decision==='deny'?'deny':'approve';for(const item of form.querySelectorAll('button'))item.disabled=true;if(decision.value==='approve'){button.textContent='正在验证 Key 并授权…';document.getElementById('submit-status').textContent='请保持此页面打开，等待跳转回 ChatGPT；不要重复提交。'}else if(button){button.textContent='正在处理…'}});</script></main>`;
}

function createNonce(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

async function defaultHandler(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  if (url.pathname !== "/authorize") {
    if (url.pathname === "/") return new Response("Garmin China Sync remote MCP. Connect with OAuth at /mcp.", { headers: { "Content-Type": "text/plain; charset=utf-8" } });
    return new Response("Not found", { status: 404 });
  }

  const oauth = env.OAUTH_PROVIDER;
  if (request.method === "GET") {
    let authStage = "parse-request";
    try {
      const authRequest = await oauth.parseAuthRequest(request);
      authStage = "describe-consent";
      const details = await oauth.describeConsent(authRequest);
      authStage = "begin-consent";
      const consent = await oauth.beginConsent(authRequest);
      const nonce = createNonce();
      const redirectOrigin = new URL(details.redirectUri).origin;
      consent.headers.set("Content-Type", "text/html; charset=utf-8");
      consent.headers.set("Cache-Control", "no-store");
      consent.headers.set("Referrer-Policy", "no-referrer");
      consent.headers.set("X-Content-Type-Options", "nosniff");
      consent.headers.set("X-Frame-Options", "DENY");
      // The form posts to this Worker, then the OAuth response redirects to the already-validated
      // client callback. Chrome can apply form-action to that redirect destination too.
      consent.headers.set("Content-Security-Policy", `default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}'; form-action 'self' ${redirectOrigin}; base-uri 'none'; frame-ancestors 'none'`);
      return new Response(authorizationPage(details.clientName, details.clientDomain, details.redirectHost, consent.handle, details.scope, nonce), { headers: consent.headers });
    } catch (error) {
      console.error("OAuth authorization page failed", {
        stage: authStage,
        name: error instanceof Error ? error.name : "unknown",
        code: error instanceof AuthorizationError ? error.code : undefined,
      });
      if (error instanceof AuthorizationError && error.redirectTo) return Response.redirect(error.redirectTo, 302);
      return html("<main><h1>无法开始授权</h1><p>请从 ChatGPT 重新连接 Garmin China Sync。</p></main>", 400);
    }
  }

  if (request.method !== "POST") return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, POST" } });
  let authStage = "read-form";
  try {
    const form = await request.formData();
    const handle = String(form.get("handle") ?? "");
    const decision = String(form.get("decision") ?? "");
    if (!handle) return html("<main><h1>授权页面已过期</h1><p>请返回 ChatGPT 重新连接。</p></main>", 400);
    if (decision !== "approve") {
      const denied = await oauth.denyConsent(request, handle);
      return new Response(null, { status: 302, headers: denied.headers });
    }
    if (form.get("consent") !== "yes") return html("<main><h1>需要你的授权</h1><p>请返回 ChatGPT 重新连接，并确认只读访问说明。</p></main>", 400);
    const key = String(form.get("garmin_key") ?? "").trim();
    if (!key || /\s/.test(key)) return html("<main><h1>Key 格式不正确</h1><p>请返回 ChatGPT 重新连接后再试。</p></main>", 400);
    // Validate at Garmin before storing anything. The bearer token is discarded immediately.
    authStage = "verify-garmin-key";
    await exchangeKeyForToken(key);
    authStage = "approve-consent";
    const approved = await oauth.approveConsent(request, handle, { scope: form.getAll("scope").map(String) });
    console.info("OAuth consent approved");
    const userId = crypto.randomUUID();
    authStage = "complete-authorization";
    const { redirectTo } = await oauth.completeAuthorization({
      request: approved.request,
      userId,
      metadata: {},
      scope: approved.request.scope,
      props: { userId, garminApiKey: key } satisfies GarminProps,
    });
    console.info("OAuth authorization completed");
    approved.headers.set("Location", redirectTo);
    return new Response(null, { status: 302, headers: approved.headers });
  } catch (error) {
    // Never reflect Garmin response bodies, URLs, submitted form values, or credential data.
    console.error("OAuth authorization form failed", {
      stage: authStage,
      name: error instanceof Error ? error.name : "unknown",
      code: error instanceof AuthorizationError ? error.code : undefined,
      description: error instanceof AuthorizationError ? error.description : undefined,
    });
    const title = authStage === "verify-garmin-key" ? "Garmin Key 验证失败" : "授权未完成";
    const message = error instanceof Error && error.message.startsWith("Garmin rejected")
      ? "Garmin rejected this Key. Check it in Garmin Connect and try again."
      : error instanceof Error && error.message.startsWith("Garmin key verification returned HTTP")
        ? "Garmin could not verify the Key right now. Try again later."
        : error instanceof AuthorizationError && authStage === "approve-consent"
          ? "授权页状态已失效或已提交过。请回到 ChatGPT 重新连接后再试。"
          : "The authorization page could not be completed. Reconnect from ChatGPT and try again.";
    return html(`<main><h1>${title}</h1><p>${escapeHtml(message)}</p><p>请关闭页面并从 ChatGPT 重新发起连接。</p></main>`, 400);
  }
}

function createServer() {
  const server = new McpServer({ name: "garmin-china-sync-cloud", version: "0.1.0" });
  const props = (): GarminProps => {
    const auth = getMcpAuthContext();
    const value = auth?.props as Partial<GarminProps> | undefined;
    if (!value?.garminApiKey || !value.userId) throw new Error("Garmin account is not connected. Reconnect through OAuth.");
    return value as GarminProps;
  };

  server.registerTool("garmin_get_activities", {
    description: "Read Garmin China activities in a date range (read-only; maximum 366 days and 100 records).",
    inputSchema: { start_date: z.string(), end_date: z.string(), limit: z.number().int().min(1).max(100).default(50) },
  }, async ({ start_date, end_date, limit }) => {
    const account = props();
    const result = await getActivities(account.garminApiKey, start_date, end_date, limit);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  });

  server.registerTool("garmin_get_activity_detail", {
    description: "Read the Garmin summary/detail object for one activity by its numeric activity ID (read-only).",
    inputSchema: { activity_id: z.number().int().positive() },
  }, async ({ activity_id }) => {
    const account = props();
    const result = await getActivityDetail(account.garminApiKey, activity_id);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  });

  server.registerTool("garmin_get_daily", {
    description: "Read Garmin China daily summary, sleep, HRV, and Body Battery records for 1–31 days (read-only).",
    inputSchema: { start_date: z.string(), end_date: z.string() },
  }, async ({ start_date, end_date }) => {
    const account = props();
    const result = await getDaily(account.garminApiKey, start_date, end_date);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  });
  return server;
}

const mcpHandler = createMcpHandler(createServer);
const providers = new Map<string, OAuthProvider<Env>>();

export default {
  fetch(request: Request, env: Env, ctx: ExecutionContext) {
    // Derive OAuth issuer/audience from the actual deployment host, so every user deploys
    // their own Worker without editing and recompiling the authorization metadata.
    const origin = new URL(request.url).origin;
    let provider = providers.get(origin);
    if (!provider) {
      provider = new OAuthProvider<Env>({
        apiRoute: "/mcp",
        apiHandler: {
          fetch(mcpRequest, bindings, executionContext) {
            return mcpHandler(mcpRequest, bindings, executionContext);
          },
        },
        defaultHandler: { fetch: defaultHandler },
        authorizeEndpoint: `${origin}/authorize`,
        tokenEndpoint: `${origin}/oauth/token`,
        clientRegistrationEndpoint: `${origin}/register`,
        scopesSupported: ["mcp:read"],
        requiredScopes: ["mcp:read"],
        accessTokenTTL: 60 * 60,
        refreshTokenTTL: 60 * 60 * 24 * 30,
        resourceMetadata: {
          resource: `${origin}/mcp`,
          authorization_servers: [origin],
          resource_name: "Garmin China Sync",
        },
        clientIdMetadataDocumentEnabled: false,
      });
      providers.set(origin, provider);
    }
    return provider.fetch(request, env, ctx);
  },
};
