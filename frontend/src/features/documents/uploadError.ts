import type { TFunction } from "i18next";

import { ApiError } from "../../api/errors";

/** Upload error -> user-facing text (R14). */
export function uploadErrorMessage(error: unknown, t: TFunction): string {
  if (!(error instanceof ApiError)) return t("common.error");
  const d = error.details;
  switch (error.code) {
    case "FILE_TOO_LARGE":
      return t("documents.errors.tooLarge", { mb: d.maxSizeMb ?? 20 });
    case "FILE_TYPE_NOT_SUPPORTED":
      return t("documents.errors.notPdf");
    case "TOO_MANY_PAGES":
      return t("documents.errors.tooManyPages", { pages: d.maxPages ?? 200 });
    case "PDF_ENCRYPTED":
      return t("documents.errors.encrypted");
    case "DOCUMENT_LIMIT_REACHED":
      return t("documents.errors.limit", { max: d.maxDocuments ?? 10 });
    case "CONSENT_REQUIRED":
      return t("documents.errors.consent");
    case "EMAIL_NOT_VERIFIED":
      return t("documents.errors.emailNotVerified");
    case "NETWORK_ERROR":
    case "TIMEOUT_ERROR":
      return t("documents.errors.network");
    default:
      return t("common.error");
  }
}
