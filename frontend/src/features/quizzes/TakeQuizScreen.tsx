import { useRouter } from "expo-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, spacing } from "../../theme/tokens";
import type { AttemptResult } from "./api";
import { quizErrorText } from "./errors";
import { useQuiz, useSubmitAttempt } from "./hooks";
import { QuestionView } from "./QuestionView";
import { QuizResult } from "./QuizResult";
import { useQuizAnswers } from "./useQuizAnswers";

/** Screen 18: answer one question at a time; leaving midway asks whether to keep the answers. */
export function TakeQuizScreen({ quizId }: { quizId: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const quiz = useQuiz(quizId);
  const submit = useSubmitAttempt(quizId);
  const progress = useQuizAnswers(quizId);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [leaving, setLeaving] = useState(false);

  const close = () =>
    router.canGoBack() ? router.back() : router.replace("/spaces");
  const answeredCount = Object.keys(progress.answers).length;
  const back = () =>
    answeredCount > 0 && !result ? setLeaving(true) : close();

  if (quiz.isPending) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  if (quiz.isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.muted}>{quizErrorText(quiz.error, t)}</Text>
        <Button label={t("common.back")} variant="secondary" onPress={close} />
      </View>
    );
  }

  const questions = quiz.data.questions;
  const question = questions[progress.index];
  const last = progress.index === questions.length - 1;

  function send() {
    submit.mutate(
      questions.map((q) => ({
        question_id: q.id,
        choice: progress.answers[q.id] ?? null,
      })),
      {
        onSuccess: (attempt) => {
          setResult(attempt);
          void progress.discard();
        },
      },
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable accessibilityRole="link" onPress={back} testID="quiz-back">
        <Text style={styles.link}>{t("common.back")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header">
        {quiz.data.title}
      </Text>

      {result ? (
        <QuizResult
          result={result}
          onRetake={() => setResult(null)}
          onDone={close}
        />
      ) : question ? (
        <>
          {progress.resumed ? (
            <Text style={styles.muted} testID="quiz-resumed">
              {t("quizzes.resumed")}
            </Text>
          ) : null}
          <Text style={styles.muted} testID="quiz-progress">
            {t("quizzes.progress", {
              current: progress.index + 1,
              total: questions.length,
            })}
          </Text>
          <QuestionView
            question={question}
            choice={progress.answers[question.id]}
            onChoose={(choice) => progress.choose(question.id, choice)}
          />
          <View style={styles.nav}>
            <Button
              label={t("citationPage.previous")}
              variant="secondary"
              disabled={progress.index === 0}
              onPress={() => progress.setIndex(progress.index - 1)}
              testID="quiz-prev"
            />
            {last ? (
              <Button
                label={t("quizzes.submit")}
                onPress={send}
                loading={submit.isPending}
                testID="quiz-submit"
              />
            ) : (
              <Button
                label={t("quizzes.next")}
                onPress={() => progress.setIndex(progress.index + 1)}
                testID="quiz-next"
              />
            )}
          </View>
          {last && answeredCount < questions.length ? (
            <Text style={styles.muted}>
              {t("quizzes.unanswered", {
                count: questions.length - answeredCount,
              })}
            </Text>
          ) : null}
          {submit.isError ? (
            <Text style={styles.error}>{quizErrorText(submit.error, t)}</Text>
          ) : null}
        </>
      ) : (
        <Text style={styles.muted}>{t("quizzes.noQuestions")}</Text>
      )}

      <Dialog
        visible={leaving}
        title={t("quizzes.leaveTitle")}
        onDismiss={() => setLeaving(false)}
        testID="quiz-leave-dialog"
      >
        <Text style={styles.text}>{t("quizzes.leaveMessage")}</Text>
        <Button
          label={t("quizzes.saveAndLeave")}
          onPress={() => void progress.saveForLater().then(close)}
          testID="quiz-leave-save"
        />
        <Button
          label={t("quizzes.discardAndLeave")}
          variant="danger"
          onPress={() => void progress.discard().then(close)}
          testID="quiz-leave-discard"
        />
        <Button
          label={t("common.cancel")}
          variant="secondary"
          onPress={() => setLeaving(false)}
        />
      </Dialog>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    gap: spacing.md,
    maxWidth: 720,
    padding: spacing.xl,
    width: "100%",
  },
  center: {
    alignItems: "center",
    flex: 1,
    gap: spacing.md,
    justifyContent: "center",
    padding: spacing.xl,
  },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  text: { color: colors.text, fontSize: fontSize.md },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  error: { color: colors.danger, fontSize: fontSize.sm },
  nav: {
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between",
  },
});
