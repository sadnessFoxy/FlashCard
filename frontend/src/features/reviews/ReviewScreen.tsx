import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import type { ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { ReviewGrade } from "./api";
import { ReviewSummary } from "./ReviewSummary";
import { useReviewSession } from "./useReviewSession";

const GRADES: {
  grade: ReviewGrade;
  variant: "danger" | "secondary" | "primary";
}[] = [
  { grade: "again", variant: "danger" },
  { grade: "hard", variant: "secondary" },
  { grade: "good", variant: "primary" },
  { grade: "easy", variant: "secondary" },
];

/** Screen 15: show the front, flip, grade. Works offline; grades sync later. */
export function ReviewScreen({
  spaceId,
  deckId,
}: {
  spaceId: string;
  deckId?: string;
}) {
  const { t } = useTranslation();
  const router = useRouter();
  const { due, session, card, finished, sync, flip, grade } = useReviewSession(
    spaceId,
    deckId,
  );
  const leave = () =>
    router.canGoBack() ? router.back() : router.replace("/spaces");

  let body: ReactNode;
  if (due.isPending) {
    body = <ActivityIndicator color={colors.primary} testID="review-loading" />;
  } else if (due.isError) {
    body = <Text style={styles.muted}>{t("review.loadError")}</Text>;
  } else if (session.queue.length === 0) {
    body = (
      <View style={styles.empty} testID="review-nothing-due">
        <Text style={styles.emptyTitle}>{t("review.nothingDueTitle")}</Text>
        <Text style={styles.muted}>{t("review.nothingDueHint")}</Text>
      </View>
    );
  } else if (finished || !card) {
    body = <ReviewSummary session={session} sync={sync} onDone={leave} />;
  } else {
    body = (
      <>
        <Text style={styles.muted} testID="review-progress">
          {t("review.progress", {
            current: session.index + 1,
            total: session.queue.length,
          })}
        </Text>
        <View style={styles.card}>
          <Text style={styles.front} testID="review-front">
            {card.front}
          </Text>
          {session.flipped ? (
            <>
              <View style={styles.divider} />
              <Text style={styles.back} testID="review-back">
                {card.back}
              </Text>
            </>
          ) : null}
        </View>
        {session.flipped ? (
          <View style={styles.grades}>
            <Text style={styles.muted}>{t("review.howWell")}</Text>
            <View style={styles.gradeRow}>
              {GRADES.map(({ grade: g, variant }) => (
                <View key={g} style={styles.gradeButton}>
                  <Button
                    label={t(`review.grades.${g}`)}
                    variant={variant}
                    onPress={() => grade(g)}
                    testID={`review-grade-${g}`}
                  />
                </View>
              ))}
            </View>
          </View>
        ) : (
          <Button
            label={t("review.flip")}
            onPress={flip}
            testID="review-flip"
          />
        )}
      </>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable accessibilityRole="link" onPress={leave}>
        <Text style={styles.link}>{t("common.back")}</Text>
      </Pressable>
      {body}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    gap: spacing.lg,
    maxWidth: 720,
    padding: spacing.xl,
    width: "100%",
  },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  empty: { alignItems: "center", gap: spacing.sm, padding: spacing.xxl },
  emptyTitle: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.lg,
    minHeight: 220,
    padding: spacing.xl,
  },
  front: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
  divider: { backgroundColor: colors.border, height: 1 },
  back: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  grades: { gap: spacing.sm },
  gradeRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  gradeButton: { flexGrow: 1 },
});
