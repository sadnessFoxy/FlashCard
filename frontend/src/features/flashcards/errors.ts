import type { TFunction } from "i18next";

import { ApiError } from "../../api/errors";

/** Localized message for a flashcard API failure (R14). */
export function flashcardErrorText(error: unknown, t: TFunction): string {
  const code = error instanceof ApiError ? error.code : null;
  switch (code) {
    case "USER_QUOTA_EXCEEDED":
      return t("cards.errors.quota");
    case "AI_TEMPORARILY_UNAVAILABLE":
    case "AI_RATE_LIMITED":
      return t("cards.errors.aiUnavailable");
    case "SOURCE_EMPTY":
      return t("cards.errors.sourceEmpty");
    case "DOCUMENT_NOT_READY":
      return t("cards.errors.notReady");
    case "DECK_FULL":
      return t("cards.errors.deckFull");
    case "NOT_FOUND":
      return t("cards.errors.notFound");
    case "NETWORK_ERROR":
    case "TIMEOUT_ERROR":
      return t("errors.networkError");
    default:
      return t("cards.errors.generic");
  }
}
