import type { TFunction } from "i18next";

import { ApiError } from "../../api/errors";

/** Map an auth API error to user-facing text (R14: never show the raw message). */
export function authErrorMessage(error: unknown, t: TFunction): string {
  if (!(error instanceof ApiError)) return t("common.error");
  switch (error.code) {
    case "INVALID_CREDENTIALS":
      return t("auth.errors.invalidCredentials");
    case "ACCOUNT_BLOCKED":
      return t("auth.errors.accountBlocked");
    case "EMAIL_UNAVAILABLE":
      return t("auth.errors.emailUnavailable");
    case "WEAK_PASSWORD":
      return t(
        `auth.errors.weakPassword.${error.details.reason ?? "too_short"}`,
      );
    case "TOO_MANY_ATTEMPTS":
      return t("auth.errors.tooManyAttempts", {
        count: Math.max(
          1,
          Math.ceil((error.details.retryAfterSeconds ?? 60) / 60),
        ),
      });
    case "INVALID_CODE":
      return t("auth.errors.invalidCode");
    case "VALIDATION_ERROR":
      return error.details.fields?.includes("email")
        ? t("auth.errors.invalidEmail")
        : t("common.error");
    case "NETWORK_ERROR":
    case "TIMEOUT_ERROR":
      return t("errors.networkError");
    default:
      return t("common.error");
  }
}
