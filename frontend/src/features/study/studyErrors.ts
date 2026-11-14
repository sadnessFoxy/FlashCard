import type { TFunction } from "i18next";

import { ApiError } from "../../api/errors";

/** Feature-specific wording; everything else is shared by the AI study features. */
export interface StudyErrorMessages {
  quota: string;
  notFound: string;
}

/** Localized message for a failure of an AI study feature (quizzes, summaries) (R14). */
export function studyErrorText(
  error: unknown,
  t: TFunction,
  messages: StudyErrorMessages,
): string {
  const code = error instanceof ApiError ? error.code : null;
  switch (code) {
    case "USER_QUOTA_EXCEEDED":
      return messages.quota;
    case "NOT_FOUND":
      return messages.notFound;
    case "AI_TEMPORARILY_UNAVAILABLE":
    case "AI_RATE_LIMITED":
      return t("quizzes.errors.aiUnavailable");
    case "SOURCE_EMPTY":
      return t("cards.errors.sourceEmpty");
    case "DOCUMENT_NOT_READY":
      return t("cards.errors.notReady");
    case "NETWORK_ERROR":
    case "TIMEOUT_ERROR":
      return t("errors.networkError");
    default:
      return t("cards.errors.generic");
  }
}
