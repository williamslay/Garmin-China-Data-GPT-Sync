import test from "node:test";
import assert from "node:assert/strict";
import { getActivities, getActivityDetail, getDaily, validateRange } from "../src/garmin.ts";

const base64url = (value) => Buffer.from(JSON.stringify(value)).toString("base64url");
const token = `e30.${base64url({ exp: Math.floor(Date.now() / 1000) + 600 })}.sig`;

test("rejects invalid, reversed, and excessive date ranges", () => {
  assert.throws(() => validateRange("2026-02-30", "2026-03-01", 31), /valid calendar date/);
  assert.throws(() => validateRange("2026-03-02", "2026-03-01", 31), /between 1 and 31/);
  assert.throws(() => validateRange("2026-01-01", "2026-02-01", 31), /between 1 and 31/);
});

test("activity list exchanges key, uses fixed China endpoints, and never returns key/token", async () => {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    if (calls.length === 1) return new Response(token, { status: 200 });
    return Response.json([{ activityId: 42 }]);
  };
  const result = await getActivities("test-key-do-not-log", "2026-10-01", "2026-10-07", 50);
  assert.deepEqual(result, [{ activityId: 42 }]);
  assert.equal(calls[0].url, "https://personal.connectapi.garmin.cn/personalapitoken-service/personal-api/personal-api-key/token");
  assert.equal(calls[0].init.headers.Authorization, "ApiKey test-key-do-not-log");
  assert.match(calls[1].url, /^https:\/\/personal\.connectapi\.garmin\.cn\/activitylist-service\//);
  assert.equal(calls[1].init.headers.Authorization, `Bearer ${token}`);
  assert.equal(calls.some((call) => call.url.includes("test-key-do-not-log")), false);
});

test("activity detail accepts only a positive ID and requests a fixed endpoint", async () => {
  await assert.rejects(() => getActivityDetail("key", 0), /positive integer/);
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return calls.length === 1 ? new Response(token) : Response.json({ activityId: 7 });
  };
  assert.deepEqual(await getActivityDetail("key", 7), { activityId: 7 });
  assert.match(calls[1].url, /\/activity-service\/activity\/7$/);
});

test("daily records combine four fixed Garmin endpoints by date", async () => {
  const calls = [];
  const records = [
    { data: [{ calendarDate: "2026-10-25", movement: { steps: { value: 1234 } } }] },
    [{ calendarDate: "2026-10-25", sleepTimeSeconds: 25200 }],
    { hrvSummaries: [{ calendarDate: "2026-10-25", lastNightAvg: 55 }] },
    [{ date: "2026-10-25", charged: 70 }],
  ];
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    return calls.length === 1 ? new Response(token) : Response.json(records[calls.length - 2]);
  };
  const result = await getDaily("key", "2026-10-25", "2026-10-25");
  assert.equal(result[0].summary.movement.steps.value, 1234);
  assert.equal(result[0].sleep.sleepTimeSeconds, 25200);
  assert.equal(result[0].hrv.lastNightAvg, 55);
  assert.deepEqual(result[0].missing_or_error, []);
  assert.equal(calls.length, 5);
  assert.ok(calls.every((url) => url.startsWith("https://personal.connectapi.garmin.cn/")));
});

test("reports rejected keys without reflecting the upstream response body", async () => {
  globalThis.fetch = async () => new Response("sensitive server body", { status: 401 });
  await assert.rejects(() => getActivities("secret", "2026-10-01", "2026-10-02", 10), (error) => {
    assert.match(error.message, /Garmin rejected this Personal API Key/);
    assert.equal(error.message.includes("sensitive server body"), false);
    assert.equal(error.message.includes("secret"), false);
    return true;
  });
});
