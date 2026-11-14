import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { sourceLabel } from "../flashcards/CardRow";
import type { AttemptResult, QuestionResult } from "./api";
import { optionLetter } from "./QuestionView";

/** Screen 19: the score (computed by the server's code) and a review of wrong answers. */
export function QuizResult({
  result,
  onRetake,
  onDone,
}: {
  result: AttemptResult;
  onRetake: () => void;
  onDone: () => void;
}) {
  const { t } = useTranslation();
  const wrong = result.results.filter((r) => !r.is_correct);

  return (
    <View style={styles.container} testID="quiz-result">
      <Text style={styles.title} accessibilityRole="header">
        {t("quizzes.resultTitle")}
      </Text>
      <Text style={styles.score} testID="quiz-score">
        {t("quizzes.score", { score: result.score, total: result.total })}
      </Text>

      {wrong.length === 0 ? (
        <Text style={styles.text}>{t("quizzes.allCorrect")}</Text>
      ) : (
        <>
          <Text style={styles.sectionTitle}>{t("quizzes.reviewWrong")}</Text>
          {wrong.map((r) => (
            <WrongAnswer key={r.question_id} result={r} />
          ))}
        </>
      )}

      <Button
        label={t("quizzes.retake")}
        variant="secondary"
        onPress={onRetake}
        testID="quiz-retake"
      />
      <Button label={t("review.done")} onPress={onDone} testID="quiz-done" />
    </View>
  );
}

function WrongAnswer({ result }: { result: QuestionResult }) {
  const { t } = useTranslation();
  const router = useRouter();
  const source = result.source;
  const canOpen = Boolean(source?.document_id && source.page);

  return (
    <View style={styles.card} testID={`quiz-wrong-${result.question_id}`}>
      <Text style={styles.prompt}>{result.prompt}</Text>
      <Text style={styles.yours}>
        {t("quizzes.yourAnswer", {
          answer:
            result.choice === null
              ? t("quizzes.blank")
              : `${optionLetter(result.choice)}. ${result.options[result.choice] ?? ""}`,
        })}
      </Text>
      <Text style={styles.correct}>
        {t("quizzes.correctAnswer", {
          answer: `${optionLetter(result.correct_index)}. ${result.options[result.correct_index] ?? ""}`,
        })}
      </Text>
      {result.explanation ? (
        <Text style={styles.text}>{result.explanation}</Text>
      ) : null}
      {source ? (
        <Pressable
          accessibilityRole="link"
          disabled={!canOpen}
          onPress={() =>
            router.push({
              pathname: "/spaces/citation",
              params: {
                documentId: source.document_id ?? "",
                page: String(source.page ?? 1),
                highlight: result.explanation,
              },
            })
          }
        >
          <Text style={canOpen ? styles.link : styles.muted}>
            {sourceLabel(source, t)}
          </Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.md },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  score: { color: colors.primary, fontSize: fontSize.xl, fontWeight: "700" },
  sectionTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "600",
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  prompt: { color: colors.text, fontSize: fontSize.md, fontWeight: "600" },
  yours: { color: colors.danger, fontSize: fontSize.sm },
  correct: { color: colors.text, fontSize: fontSize.sm, fontWeight: "600" },
  text: { color: colors.text, fontSize: fontSize.md },
  link: { color: colors.primary, fontSize: fontSize.sm },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
});
