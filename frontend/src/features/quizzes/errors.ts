import type { TFunction } from "i18next";

import { studyErrorText } from "../study/studyErrors";

export function quizErrorText(error: unknown, t: TFunction): string {
  return studyErrorText(error, t, {
    quota: t("quizzes.errors.quota"),
    notFound: t("quizzes.errors.notFound"),
  });
}
