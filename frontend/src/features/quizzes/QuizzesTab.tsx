import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { QuizSummary } from "./api";
import { useQuizzes } from "./hooks";

export function pageRangeLabel(
  quiz: Pick<QuizSummary, "page_start" | "page_end">,
  t: ReturnType<typeof useTranslation>["t"],
): string {
  if (!quiz.page_start && !quiz.page_end) return t("quizzes.wholeDocument");
  if (quiz.page_start === quiz.page_end)
    return t("chat.page", { page: quiz.page_start });
  return t("chat.pages", {
    start: quiz.page_start ?? 1,
    end: quiz.page_end ?? "…",
  });
}

/** The quizzes of a space: create a new one or take one again. */
export function QuizzesTab({ spaceId }: { spaceId: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const quizzes = useQuizzes(spaceId);

  if (quizzes.isPending) {
    return <ActivityIndicator color={colors.primary} />;
  }
  if (quizzes.isError) {
    return <Text style={styles.muted}>{t("quizzes.loadError")}</Text>;
  }

  return (
    <View style={styles.container}>
      <Button
        label={t("quizzes.create")}
        onPress={() =>
          router.push({ pathname: "/spaces/quizzes/new", params: { spaceId } })
        }
        testID="quizzes-create"
      />
      {quizzes.data.items.length === 0 ? (
        <View style={styles.empty} testID="quizzes-empty">
          <Text style={styles.emptyTitle}>{t("quizzes.emptyTitle")}</Text>
          <Text style={styles.muted}>{t("quizzes.emptyHint")}</Text>
        </View>
      ) : (
        quizzes.data.items.map((quiz) => (
          <Pressable
            key={quiz.id}
            style={styles.row}
            accessibilityRole="button"
            onPress={() =>
              router.push({
                pathname: "/spaces/quizzes/[quizId]",
                params: { quizId: quiz.id },
              })
            }
            testID={`quiz-${quiz.id}`}
          >
            <Text style={styles.name}>{quiz.title}</Text>
            <Text style={styles.muted}>
              {pageRangeLabel(quiz, t)} ·{" "}
              {t("quizzes.questionCount", { count: quiz.question_count })}
              {quiz.last_score !== null
                ? ` · ${t("quizzes.lastScore", { score: quiz.last_score, total: quiz.question_count })}`
                : ""}
            </Text>
          </Pressable>
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.md },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  empty: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderStyle: "dashed",
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.xxl,
  },
  emptyTitle: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
  row: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  name: { color: colors.text, fontSize: fontSize.md, fontWeight: "600" },
});
