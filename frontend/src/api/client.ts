/**
 * API client duy nhất cho toàn bộ frontend.
 * - Gắn Bearer token từ secure storage (native) hoặc dùng cookie (web)
 * - Timeout và retry khi lỗi mạng
 * - Auto refresh token khi nhận 401
 * Tuân thủ R12: token không lưu trong AsyncStorage/localStorage.
 */

import { Platform } from "react-native";
import { config } from "../config";
import {
  ApiError,
  NetworkError,
  TimeoutError,
  parseApiError,
} from "./errors";

// Import platform-specific session storage
// Metro sẽ chọn đúng file theo nền tảng (.native.ts / .web.ts)
import {
  getAccessToken,
  getRefreshToken,
  saveAccessToken,
  saveRefreshToken,
  clearTokens,
} from "../storage/session";

const DEFAULT_TIMEOUT_MS = 30_000;
const STREAM_TIMEOUT_MS = 120_000;
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1_000;

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface RequestOptions {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeoutMs?: number;
  skipAuth?: boolean;
  isStream?: boolean;
}

let isRefreshing = false;
let refreshSubscribers: Array<(token: string | null) => void> = [];

function subscribeTokenRefresh(callback: (token: string | null) => void): void {
  refreshSubscribers.push(callback);
}

function notifyRefreshSubscribers(token: string | null): void {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken && Platform.OS !== "web") {
    return null;
  }

  const response = await fetch(`${config.apiUrl}/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // Native: gửi refresh token trong body; Web: cookie tự động gửi
    body: Platform.OS !== "web"
      ? JSON.stringify({ refresh_token: refreshToken })
      : undefined,
    credentials: Platform.OS === "web" ? "include" : "omit",
  });

  if (!response.ok) {
    await clearTokens();
    return null;
  }

  if (Platform.OS !== "web") {
    const data = (await response.json()) as {
      access_token: string;
      refresh_token?: string;
    };
    await saveAccessToken(data.access_token);
    if (data.refresh_token) {
      await saveRefreshToken(data.refresh_token);
    }
    return data.access_token;
  }

  // Web: backend set cookie tự động
  return "__cookie__";
}

async function buildHeaders(
  skipAuth: boolean,
  extraHeaders: Record<string, string> = {}
): Promise<HeadersInit> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...extraHeaders,
  };

  if (!skipAuth && Platform.OS !== "web") {
    const token = await getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  return headers;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryableError(error: unknown): boolean {
  if (error instanceof NetworkError || error instanceof TimeoutError) {
    return true;
  }
  return false;
}

async function executeRequest(
  url: string,
  options: RequestOptions,
  retryCount = 0
): Promise<Response> {
  const {
    method = "GET",
    body,
    headers: extraHeaders = {},
    timeoutMs = DEFAULT_TIMEOUT_MS,
    skipAuth = false,
    isStream = false,
  } = options;

  const controller = new AbortController();
  const signal = options.signal;

  // Timeout
  const timeoutId = setTimeout(() => controller.abort("timeout"), timeoutMs);
  if (signal) {
    signal.addEventListener("abort", () => controller.abort(signal.reason));
  }

  try {
    const headers = await buildHeaders(skipAuth, extraHeaders);
    if (isStream) {
      (headers as Record<string, string>)["Accept"] = "text/event-stream";
    }

    const response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
      credentials: Platform.OS === "web" ? "include" : "omit",
    });

    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error && error.name === "AbortError") {
      if (controller.signal.reason === "timeout") {
        throw new TimeoutError();
      }
      throw error;
    }

    const networkError = new NetworkError(
      error instanceof Error ? error.message : "Network request failed"
    );

    if (retryCount < MAX_RETRIES && isRetryableError(networkError)) {
      await sleep(RETRY_DELAY_MS * (retryCount + 1));
      return executeRequest(url, options, retryCount + 1);
    }

    throw networkError;
  }
}

export async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const url = `${config.apiUrl}${path}`;
  const timeoutMs = options.isStream ? STREAM_TIMEOUT_MS : DEFAULT_TIMEOUT_MS;

  let response = await executeRequest(url, { ...options, timeoutMs });

  // Auto refresh token khi nhận 401
  if (response.status === 401 && !options.skipAuth) {
    if (!isRefreshing) {
      isRefreshing = true;

      const newToken = await refreshAccessToken().catch(() => null);
      isRefreshing = false;
      notifyRefreshSubscribers(newToken);

      if (!newToken) {
        // Refresh thất bại - người dùng cần đăng nhập lại
        throw new ApiError("UNAUTHORIZED", "Session expired", 401);
      }
    } else {
      // Chờ token refresh đang chạy
      await new Promise<void>((resolve) => {
        subscribeTokenRefresh(() => resolve());
      });
    }

    // Thử lại request với token mới
    response = await executeRequest(url, { ...options, timeoutMs });
  }

  if (!response.ok) {
    let errorBody: unknown;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = { code: "INTERNAL_SERVER_ERROR", message: response.statusText };
    }
    throw parseApiError(response, errorBody);
  }

  // Stream response - trả về response thô để caller đọc
  if (options.isStream) {
    return response as unknown as T;
  }

  // Empty response (204 No Content)
  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "GET" }),

  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    request<T>(path, { ...options, method: "POST", body }),

  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    request<T>(path, { ...options, method: "PUT", body }),

  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    request<T>(path, { ...options, method: "PATCH", body }),

  delete: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "DELETE" }),

  stream: (path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "isStream">) =>
    request<Response>(path, { ...options, method: "POST", body, isStream: true }),
};
