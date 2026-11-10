/**
 * The only module allowed to call the network (docs/ARCHITECTURE.md).
 * - Native: Bearer token from secure storage. Web: httpOnly cookies (R12).
 * - Every request sends X-Client-Platform so the backend picks body tokens or cookies.
 * - On 401 it refreshes once (shared by concurrent requests) and retries; if refresh
 *   fails it clears the session and notifies the auth store.
 */

import { Platform } from "react-native";

import { config } from "../config";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  saveAccessToken,
  saveRefreshToken,
} from "../storage/session";
import { ApiError, NetworkError, TimeoutError, parseApiError } from "./errors";

const DEFAULT_TIMEOUT_MS = 30_000;
const STREAM_TIMEOUT_MS = 120_000;
const MAX_NETWORK_RETRIES = 2;
const RETRY_DELAY_MS = 1_000;

const IS_WEB = Platform.OS === "web";
export const CLIENT_PLATFORM = IS_WEB ? "web" : "native";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface RequestOptions {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeoutMs?: number;
  /** Skip the Bearer header and the 401 refresh dance (auth endpoints). */
  skipAuth?: boolean;
  isStream?: boolean;
}

/** Tokens returned to native clients; absent on web. */
export interface SessionTokens {
  access_token?: string;
  refresh_token?: string;
}

let sessionExpiredListener: (() => void) | null = null;

/** The auth store registers here to learn that the session is gone. */
export function onSessionExpired(listener: (() => void) | null): void {
  sessionExpiredListener = listener;
}

export async function storeSessionTokens(tokens: SessionTokens): Promise<void> {
  if (IS_WEB) return;
  if (tokens.access_token) await saveAccessToken(tokens.access_token);
  if (tokens.refresh_token) await saveRefreshToken(tokens.refresh_token);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function buildHeaders(
  options: RequestOptions,
): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    Accept: options.isStream ? "text/event-stream" : "application/json",
    "X-Client-Platform": CLIENT_PLATFORM,
    ...options.headers,
  };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (!options.skipAuth && !IS_WEB) {
    const token = await getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function send(
  url: string,
  options: RequestOptions,
  attempt = 0,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutMs =
    options.timeoutMs ??
    (options.isStream ? STREAM_TIMEOUT_MS : DEFAULT_TIMEOUT_MS);
  const timeoutId = setTimeout(() => controller.abort("timeout"), timeoutMs);
  options.signal?.addEventListener("abort", () =>
    controller.abort(options.signal?.reason),
  );

  try {
    return await fetch(url, {
      method: options.method ?? "GET",
      headers: await buildHeaders(options),
      body:
        options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
      credentials: IS_WEB ? "include" : "omit",
    });
  } catch (error) {
    if (controller.signal.aborted) {
      if (controller.signal.reason === "timeout") throw new TimeoutError();
      throw error; // cancelled by the caller
    }
    if (attempt < MAX_NETWORK_RETRIES) {
      await sleep(RETRY_DELAY_MS * (attempt + 1));
      return send(url, options, attempt + 1);
    }
    throw new NetworkError(
      error instanceof Error ? error.message : "Network request failed",
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

let refreshInFlight: Promise<boolean> | null = null;

async function doRefresh(): Promise<boolean> {
  const refreshToken = IS_WEB ? null : await getRefreshToken();
  if (!IS_WEB && !refreshToken) return false;
  try {
    const response = await send(`${config.apiUrl}/v1/auth/refresh`, {
      method: "POST",
      skipAuth: true,
      ...(IS_WEB ? {} : { body: { refresh_token: refreshToken } }),
    });
    if (!response.ok) return false;
    await storeSessionTokens((await response.json()) as SessionTokens);
    return true;
  } catch {
    return false;
  }
}

/** Single-flight refresh: concurrent 401s share one call. */
export function refreshSession(): Promise<boolean> {
  refreshInFlight ??= doRefresh().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

export async function endLocalSession(): Promise<void> {
  await clearTokens();
  sessionExpiredListener?.();
}

async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // non-JSON error body
  }
  return parseApiError(response.status, body);
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const url = `${config.apiUrl}${path}`;
  let response = await send(url, options);

  if (response.status === 401 && !options.skipAuth) {
    if (await refreshSession()) {
      response = await send(url, options);
    } else {
      await endLocalSession();
      throw await toApiError(response);
    }
  }

  if (!response.ok) throw await toApiError(response);
  if (options.isStream) return response as unknown as T;
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, "method">,
  ) => request<T>(path, { ...options, method: "POST", body }),
  put: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, "method">,
  ) => request<T>(path, { ...options, method: "PUT", body }),
  patch: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, "method">,
  ) => request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(
    path: string,
    options?: Omit<RequestOptions, "method" | "body">,
  ) => request<T>(path, { ...options, method: "DELETE" }),
  stream: (
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, "method" | "isStream">,
  ) =>
    request<Response>(path, {
      ...options,
      method: "POST",
      body,
      isStream: true,
    }),
};
