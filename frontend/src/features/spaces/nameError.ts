import type { TFunction } from "i18next";

import { ApiError } from "../../api/errors";

export const SPACE_NAME_MAX = 100;

/** Same normalization as the server, for instant validation. */
export function normalizeSpaceName(raw: string): string {
  return raw.normalize("NFC").replace(/\s+/g, " ").trim();
}

export function localNameError(raw: string, t: TFunction): string | null {
  const name = normalizeSpaceName(raw);
  if (!name) return t("spaces.errors.nameRequired");
  if (name.length > SPACE_NAME_MAX)
    return t("spaces.errors.nameTooLong", { max: SPACE_NAME_MAX });
  return null;
}

export function apiNameError(error: unknown, t: TFunction): string {
  if (error instanceof ApiError) {
    if (error.code === "SPACE_NAME_TAKEN") return t("spaces.errors.nameTaken");
    if (error.code === "VALIDATION_ERROR")
      return t("spaces.errors.nameRequired");
    if (error.isNetworkError) return t("errors.networkError");
  }
  return t("common.error");
}
