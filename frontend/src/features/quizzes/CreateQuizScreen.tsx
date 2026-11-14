import { useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { ChipGroup } from "../../components/ui/ChipGroup";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { useDocuments } from "../documents/hooks";
import { quizErrorText } from "./errors";
import { useCreateQuiz } from "./hooks";

const COUNTS = ["5", "10", "15", "20"];

function toPage(text: string): number | null {
  const n = Number(text);
  return Number.isInteger(n) && n >= 1 ? n : null;
}

/** Screen 17: pick a document, pages and how many questions; the AI writes the quiz. */
export function CreateQuizScreen({ spaceId }: { spaceId: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const documents = useDocuments(spaceId);
  const create = useCreateQuiz();
  const ready = useMemo(
    () => (documents.data?.items ?? []).filter((d) => d.status === "READY"),
    [documents.data],
  );
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [pageFrom, setPageFrom] = useState("");
  const [pageTo, setPageTo] = useState("");
  const [count, setCount] = useState("10");
  const chosen = documentId ?? ready[0]?.id ?? null;

  function submit() {
    if (!chosen) return;
    create.mutate(
      {
        space_id: spaceId,
        document_id: chosen,
        page_start: toPage(pageFrom),
        page_end: toPage(pageTo),
        question_count: Number(count),
      },
      {
        onSuccess: (quiz) =>
          router.replace({
            pathname: "/spaces/quizzes/[quizId]",
            params: { quizId: quiz.id },
          }),
      },
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable
        accessibilityRole="link"
        onPress={() =>
          router.canGoBack() ? router.back() : router.replace("/spaces")
        }
      >
        <Text style={styles.link}>{t("common.back")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header">
        {t("quizzes.createTitle")}
      </Text>

      {ready.length === 0 ? (
        <Text style={styles.muted} testID="quiz-no-documents">
          {t("chat.noDocumentsHint")}
        </Text>
      ) : (
        <>
          <Text style={styles.label}>{t("cards.sourceTitle")}</Text>
          <ChipGroup
            options={ready.map((d) => ({ value: d.id, label: d.filename }))}
            value={chosen}
            onChange={setDocumentId}
            testID="quiz-doc"
          />
          <View style={styles.pages}>
            <View style={styles.pageField}>
              <TextField
                label={t("cards.pageFrom")}
                value={pageFrom}
                onChangeText={setPageFrom}
                keyboardType="number-pad"
                testID="quiz-page-from"
              />
            </View>
            <View style={styles.pageField}>
              <TextField
                label={t("cards.pageTo")}
                value={pageTo}
                onChangeText={setPageTo}
                keyboardType="number-pad"
                testID="quiz-page-to"
              />
            </View>
          </View>
          <Text style={styles.label}>{t("quizzes.countLabel")}</Text>
          <ChipGroup
            options={COUNTS.map((c) => ({ value: c, label: c }))}
            value={count}
            onChange={setCount}
          />
          <Text style={styles.muted}>{t("quizzes.usesQuota")}</Text>
          <Button
            label={t("quizzes.generate")}
            onPress={submit}
            loading={create.isPending}
            testID="quiz-generate"
          />
          {create.isPending ? (
            <Text style={styles.muted}>{t("quizzes.generating")}</Text>
          ) : null}
          {create.isError ? (
            <Text
              style={styles.error}
              accessibilityRole="alert"
              testID="quiz-error"
            >
              {quizErrorText(create.error, t)}
            </Text>
          ) : null}
        </>
      )}
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
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  label: { color: colors.text, fontSize: fontSize.sm, fontWeight: "600" },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  pages: { flexDirection: "row", gap: spacing.md },
  pageField: { flex: 1 },
  error: {
    backgroundColor: colors.dangerBg,
    borderRadius: radius.md,
    color: colors.danger,
    fontSize: fontSize.sm,
    padding: spacing.md,
  },
});
