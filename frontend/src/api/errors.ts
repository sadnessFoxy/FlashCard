/**
 * Phân loại và xử lý lỗi API.
 * Mã lỗi khớp với contract/openapi.yaml.
 */

export type ApiErrorCode =
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "VALIDATION_ERROR"
  | "INTERNAL_SERVER_ERROR"
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

export interface ApiErrorBody {
  code: ApiErrorCode;
  message: string;
  details?: Record<string, unknown>;
  quota_remaining?: number;
  quota_reset_at?: string;
}

export class ApiError extends Error {
  constructor(
    public readonly code: ApiErrorCode,
    message: string,
    public readonly statusCode?: number,
    public readonly details?: Record<string, unknown>,
    public readonly quotaRemaining?: number,
    public readonly quotaResetAt?: Date
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

export function parseApiError(response: Response, body: unknown): ApiError {
  const errorBody = body as Partial<ApiErrorBody>;
  const code: ApiErrorCode = errorBody.code ?? "INTERNAL_SERVER_ERROR";
  const message = errorBody.message ?? "An unexpected error occurred";
  const quotaResetAt = errorBody.quota_reset_at
    ? new Date(errorBody.quota_reset_at)
    : undefined;

  return new ApiError(
    code,
    message,
    response.status,
    errorBody.details,
    errorBody.quota_remaining,
    quotaResetAt
  );
}
