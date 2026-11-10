/**
 * API client session handling (spec f2 criterion 8): concurrent 401s share one refresh,
 * and a failed refresh ends the local session.
 */
import { api, onSessionExpired } from "../../src/api/client";
import { ApiError } from "../../src/api/errors";
import * as session from "../../src/storage/session";

jest.mock("../../src/config", () => ({
  config: { apiUrl: "http://api.test" },
}));
jest.mock("../../src/storage/session", () => {
  const store: Record<string, string | null> = {
    access: "old-access",
    refresh: "old-refresh",
  };
  return {
    getAccessToken: jest.fn(async () => store.access),
    getRefreshToken: jest.fn(async () => store.refresh),
    saveAccessToken: jest.fn(async (t: string) => {
      store.access = t;
    }),
    saveRefreshToken: jest.fn(async (t: string) => {
      store.refresh = t;
    }),
    clearTokens: jest.fn(async () => {
      store.access = null;
      store.refresh = null;
    }),
    __store: store,
  };
});

const store = (session as unknown as { __store: Record<string, string | null> })
  .__store;

function json(status: number, body: unknown): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fetchMock = jest.fn<Promise<Response>, [string, RequestInit]>();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  store.access = "old-access";
  store.refresh = "old-refresh";
  onSessionExpired(null);
});

function authHeader(init: RequestInit): string | undefined {
  return (init.headers as Record<string, string>).Authorization;
}

it("sends the platform header and the bearer token", async () => {
  fetchMock.mockResolvedValue(json(200, { ok: true }));

  await api.get("/v1/me");

  const init = fetchMock.mock.calls[0][1];
  expect((init.headers as Record<string, string>)["X-Client-Platform"]).toBe(
    "native",
  );
  expect(authHeader(init)).toBe("Bearer old-access");
});

it("refreshes once for concurrent 401s and retries every request", async () => {
  let refreshCalls = 0;
  fetchMock.mockImplementation(async (url, init) => {
    if (url.endsWith("/v1/auth/refresh")) {
      refreshCalls += 1;
      await new Promise((r) => setTimeout(r, 10));
      return json(200, {
        access_token: "new-access",
        refresh_token: "new-refresh",
      });
    }
    return authHeader(init) === "Bearer new-access"
      ? json(200, { url })
      : json(401, { code: "UNAUTHORIZED", message: "expired" });
  });

  const results = await Promise.all([
    api.get("/v1/a"),
    api.get("/v1/b"),
    api.get("/v1/c"),
  ]);

  expect(refreshCalls).toBe(1);
  expect(results).toHaveLength(3);
  expect(store.refresh).toBe("new-refresh");
  const refreshBody = fetchMock.mock.calls.find(([u]) =>
    u.endsWith("/refresh"),
  )?.[1].body;
  expect(JSON.parse(String(refreshBody))).toEqual({
    refresh_token: "old-refresh",
  });
});

it("ends the session when refresh fails", async () => {
  const expired = jest.fn();
  onSessionExpired(expired);
  fetchMock.mockImplementation(async (url) =>
    url.endsWith("/v1/auth/refresh")
      ? json(401, { code: "INVALID_REFRESH_TOKEN", message: "x" })
      : json(401, { code: "UNAUTHORIZED", message: "x" }),
  );

  await expect(api.get("/v1/me")).rejects.toMatchObject({
    code: "UNAUTHORIZED",
  });

  expect(expired).toHaveBeenCalledTimes(1);
  expect(store.access).toBeNull();
  expect(store.refresh).toBeNull();
});

it("does not try to refresh for auth endpoints", async () => {
  fetchMock.mockResolvedValue(
    json(401, { code: "INVALID_CREDENTIALS", message: "x" }),
  );

  const error = await api
    .post("/v1/auth/login", { email: "a", password: "b" }, { skipAuth: true })
    .catch((e: unknown) => e);

  expect(error).toBeInstanceOf(ApiError);
  expect((error as ApiError).code).toBe("INVALID_CREDENTIALS");
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(authHeader(fetchMock.mock.calls[0][1])).toBeUndefined();
});

it("parses rate-limit details", async () => {
  fetchMock.mockResolvedValue(
    json(429, {
      code: "TOO_MANY_ATTEMPTS",
      message: "x",
      retry_after_seconds: 120,
    }),
  );

  const error = (await api
    .post("/v1/auth/login", {}, { skipAuth: true })
    .catch((e) => e)) as ApiError;

  expect(error.details.retryAfterSeconds).toBe(120);
});
