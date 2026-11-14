import type { TFunction } from "i18next";

import { studyErrorText } from "../study/studyErrors";

export function summaryErrorText(error: unknown, t: TFunction): string {
  return studyErrorText(error, t, {
    quota: t("summaries.errors.quota"),
    notFound: t("documents.notFound"),
  });
}
