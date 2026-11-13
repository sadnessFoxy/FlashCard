import type { TFunction } from "i18next";

import type { Citation } from "./api";
import type { ChatFailure } from "./useAskQuestion";

export function pagesLabel(c: Citation, t: TFunction): string {
  return c.page_start === c.page_end
    ? t("chat.page", { page: c.page_start })
    : t("chat.pages", { start: c.page_start, end: c.page_end });
}

/** Maps an API error code to a localized message (R14). */
export function chatErrorText(
  failure: ChatFailure,
  t: TFunction,
  language: string,
): string {
  switch (failure.code) {
    case "USER_QUOTA_EXCEEDED":
      return failure.resetAt
        ? t("chat.errors.quotaUntil", {
            time: failure.resetAt.toLocaleString(language, {
              hour: "2-digit",
              minute: "2-digit",
              day: "2-digit",
              month: "2-digit",
            }),
          })
        : t("chat.errors.quota");
    case "AI_TEMPORARILY_UNAVAILABLE":
    case "AI_RATE_LIMITED":
      return t("chat.errors.aiUnavailable");
    case "NETWORK_ERROR":
    case "TIMEOUT_ERROR":
      return t("chat.errors.network");
    case "NOT_FOUND":
      return t("chat.errors.notFound");
    case "VALIDATION_ERROR":
      return t("chat.errors.invalid");
    default:
      return t("chat.errors.generic");
  }
}
