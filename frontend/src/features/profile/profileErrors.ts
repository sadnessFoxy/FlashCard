import type { TFunction } from "i18next";

import { ApiError } from "../../api/errors";
import { authErrorMessage } from "../auth/errorMessage";

/** Messages for password change and account deletion; falls back to the auth messages. */
export function profileErrorText(error: unknown, t: TFunction): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case "INVALID_PASSWORD":
        return t("profile.errors.invalidPassword");
      case "NO_PASSWORD":
        return t("profile.errors.noPassword");
      case "CONFIRMATION_MISMATCH":
        return t("profile.errors.confirmationMismatch");
    }
  }
  return authErrorMessage(error, t);
}
