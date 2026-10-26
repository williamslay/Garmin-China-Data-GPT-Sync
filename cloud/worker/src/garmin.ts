const BASE_URL = "https://personal.connectapi.garmin.cn";
const TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token";

export class GarminError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GarminError";
  }
}

function validDate(value: string, name: string): Date {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new GarminError(`${name} must use YYYY-MM-DD.`);
  const date = new Date(`${value}T00:00:00Z`);
  if (!Number.isFinite(date.valueOf()) || date.toISOString().slice(0, 10) !== value) {
    throw new GarminError(`${name} is not a valid calendar date.`);
  }
  return date;
}

export function validateRange(startDate: string, endDate: string, maximumDays: number): void {
  const start = validDate(startDate, "start_date");
  const end = validDate(endDate, "end_date");
  const days = (end.valueOf() - start.valueOf()) / 86_400_000 + 1;
  if (days < 1 || days > maximumDays) throw new GarminError(`Date range must be between 1 and ${maximumDays} days.`);
}

async function request(path: string, token: string, params?: Record<string, string>): Promise<unknown> {
  // All callers pass fixed endpoint templates below; users cannot supply an upstream URL or path.
  const url = new URL(path, BASE_URL);
  for (const [key, value] of Object.entries(params ?? {})) url.searchParams.set(key, value);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      redirect: "manual",
      signal: AbortSignal.timeout(20_000),
    });
  } catch (error) {
    throw new GarminError(`Garmin request failed (${error instanceof Error ? error.name : "network error"}).`);
  }
  if (response.status !== 200) throw new GarminError(`Garmin API returned HTTP ${response.status} for ${path}.`);
  try {
    return await response.json();
  } catch {
    throw new GarminError("Garmin API returned invalid JSON.");
  }
}

export async function exchangeKeyForToken(apiKey: string): Promise<string> {
  let response: Response;
  try {
    response = await fetch(new URL(TOKEN_PATH, BASE_URL), {
      method: "POST",
      headers: { Authorization: `ApiKey ${apiKey}`, Accept: "*/*" },
      redirect: "manual",
      signal: AbortSignal.timeout(20_000),
    });
  } catch (error) {
    throw new GarminError(`Garmin key verification failed (${error instanceof Error ? error.name : "network error"}).`);
  }
  if (response.status !== 200) {
    if (response.status === 401 || response.status === 403) throw new GarminError("Garmin rejected this Personal API Key. Check it or create a new one.");
    throw new GarminError(`Garmin key verification returned HTTP ${response.status}.`);
  }
  const token = (await response.text()).trim();
  const segments = token.split(".");
  if (segments.length !== 3 || !segments[1]) throw new GarminError("Garmin returned an invalid access token.");
  try {
    const base64 = segments[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    const payload = JSON.parse(atob(padded));
    if (typeof payload.exp !== "number" || payload.exp * 1000 <= Date.now()) throw new Error("expired");
  } catch {
    throw new GarminError("Garmin returned an invalid or expired access token.");
  }
  return token;
}

export async function getActivities(apiKey: string, startDate: string, endDate: string, limit: number) {
  validateRange(startDate, endDate, 366);
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new GarminError("limit must be an integer from 1 to 100.");
  const token = await exchangeKeyForToken(apiKey);
  const payload = await request("/activitylist-service/activities/search/activities", token, {
    start: "0", limit: String(limit), startDate, endDate,
  });
  if (!Array.isArray(payload)) throw new GarminError("Garmin activity list had an unexpected response shape.");
  return payload;
}

export async function getActivityDetail(apiKey: string, activityId: number) {
  if (!Number.isSafeInteger(activityId) || activityId < 1) throw new GarminError("activity_id must be a positive integer.");
  const token = await exchangeKeyForToken(apiKey);
  return request(`/activity-service/activity/${activityId}`, token);
}

function rows(payload: unknown, wrapper?: string): Record<string, unknown>[] {
  const value = wrapper && payload && typeof payload === "object" ? (payload as Record<string, unknown>)[wrapper] : payload;
  if (!Array.isArray(value) || value.some((item) => !item || typeof item !== "object" || Array.isArray(item))) {
    throw new GarminError("Garmin daily data had an unexpected response shape.");
  }
  return value as Record<string, unknown>[];
}

export async function getDaily(apiKey: string, startDate: string, endDate: string) {
  validateRange(startDate, endDate, 31);
  const token = await exchangeKeyForToken(apiKey);
  const query = { startDate, endDate };
  const calls = await Promise.allSettled([
    request("/usersummary-service/v2/dailysummaries", token, query),
    request("/sleep-service/sleep/dailySleepSummariesByDate", token, query),
    request(`/hrv-service/hrv/daily/${startDate}/${endDate}`, token),
    request("/wellness-service/wellness/bodyBattery/reports/daily", token, query),
  ]);
  const output: Record<string, Record<string, unknown>> = {};
  const errors: Record<string, string[]> = {};
  const days: string[] = [];
  const first = validDate(startDate, "start_date");
  const last = validDate(endDate, "end_date");
  for (let day = first; day <= last; day = new Date(day.valueOf() + 86_400_000)) {
    const date = day.toISOString().slice(0, 10);
    days.push(date);
    output[date] = {};
    errors[date] = [];
  }
  const kinds = ["summary", "sleep", "hrv", "body_battery"] as const;
  const wrappers = ["data", undefined, "hrvSummaries", undefined] as const;
  const dateKeys = ["calendarDate", "calendarDate", "calendarDate", "date"] as const;
  for (let i = 0; i < calls.length; i += 1) {
    const call = calls[i];
    const kind = kinds[i];
    if (call.status === "rejected") {
      for (const date of days) errors[date].push(`${kind}: ${call.reason instanceof Error ? call.reason.message : "request failed"}`);
      continue;
    }
    try {
      const results = rows(call.value, wrappers[i]);
      const matched = new Set<string>();
      for (const item of results) {
        const date = item[dateKeys[i]];
        if (typeof date === "string" && output[date]) {
          if (matched.has(date)) throw new GarminError(`${kind} returned duplicate records for ${date}.`);
          output[date][kind] = item;
          matched.add(date);
        }
      }
      for (const date of days) if (!matched.has(date)) errors[date].push(`${kind}: no data returned`);
    } catch (error) {
      for (const date of days) {
        delete output[date][kind];
        errors[date].push(`${kind}: ${error instanceof Error ? error.message : "unexpected response"}`);
      }
    }
  }
  return days.map((date) => ({ date, ...output[date], missing_or_error: errors[date] }));
}
