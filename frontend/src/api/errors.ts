/**
 * API error model. Codes match contract/openapi.yaml; screens map `code` to i18n text
 * (R14) and never show `message`, which is developer-facing.
 */

export type ApiErrorCode =
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "VALIDATION_ERROR"
  | "INTERNAL_SERVER_ERROR"
  | "INVALID_CREDENTIALS"
  | "ACCOUNT_BLOCKED"
  | "EMAIL_UNAVAILABLE"
  | "WEAK_PASSWORD"
  | "TOO_MANY_ATTEMPTS"
  | "INVALID_REFRESH_TOKEN"
  | "CSRF_REJECTED"
  | "SPACE_NAME_TAKEN"
  | "AI_TEMPORARILY_UNAVAILABLE"
  | "AI_RATE_LIMITED"
  | "USER_QUOTA_EXCEEDED"
  | "CONTEXT_TOO_LONG"
  | "DOCUMENT_PROCESSING_FAILED"
  | "DOCUMENT_NOT_READY"
  | "FILE_TOO_LARGE"
  | "FILE_TYPE_NOT_SUPPORTED"
  | "NETWORK_ERROR"
  | "TIMEOUT_ERROR";

export type WeakPasswordReason =
  "too_short" | "too_long" | "too_common" | "same_as_email";

export interface ApiErrorBody {
  code: ApiErrorCode;
  message: string;
  reason?: WeakPasswordReason;
  retry_after_seconds?: number;
  errors?: { field: string; type: string }[];
  quota_remaining?: number;
  quota_reset_at?: string;
}

export interface ApiErrorDetails {
  reason?: WeakPasswordReason;
  retryAfterSeconds?: number;
  fields?: string[];
  quotaRemaining?: number;
  quotaResetAt?: Date;
}

export class ApiError extends Error {
  constructor(
    public readonly code: ApiErrorCode,
    message: string,
    public readonly statusCode?: number,
    public readonly details: ApiErrorDetails = {},
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isUnauthorized(): boolean {
    return this.code === "UNAUTHORIZED";
  }

  get isQuotaError(): boolean {
    return (
      this.code === "USER_QUOTA_EXCEEDED" ||
      this.code === "AI_RATE_LIMITED" ||
      this.code === "AI_TEMPORARILY_UNAVAILABLE"
    );
  }

  get isNetworkError(): boolean {
    return this.code === "NETWORK_ERROR" || this.code === "TIMEOUT_ERROR";
  }
}

export class NetworkError extends ApiError {
  constructor(message: string) {
    super("NETWORK_ERROR", message);
    this.name = "NetworkError";
  }
}

export class TimeoutError extends ApiError {
  constructor() {
    super("TIMEOUT_ERROR", "Request timed out");
    this.name = "TimeoutError";
  }
}

export function parseApiError(status: number, body: unknown): ApiError {
  const b = (body ?? {}) as Partial<ApiErrorBody>;
  const details: ApiErrorDetails = {};
  if (b.reason) details.reason = b.reason;
  if (b.retry_after_seconds) details.retryAfterSeconds = b.retry_after_seconds;
  if (b.errors) details.fields = b.errors.map((e) => e.field);
  if (b.quota_remaining !== undefined)
    details.quotaRemaining = b.quota_remaining;
  if (b.quota_reset_at) details.quotaResetAt = new Date(b.quota_reset_at);
  return new ApiError(
    b.code ?? "INTERNAL_SERVER_ERROR",
    b.message ?? "Unexpected error",
    status,
    details,
  );
}
