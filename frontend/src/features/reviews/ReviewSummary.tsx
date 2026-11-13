import { useTranslation } from "react-i18next";
import { StyleSheet, Text, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { SessionState } from "./session";
import type { SyncState } from "./useReviewSession";

const GRADES = ["again", "hard", "good", "easy"] as const;

/** Screen 16: what the session covered, the hard cards and when to come back. */
export function ReviewSummary({
  session,
  sync,
  onDone,
}: {
  session: SessionState;
  sync: SyncState;
  onDone: () => void;
}) {
  const { t, i18n } = useTranslation();
  const reviewed = GRADES.reduce((sum, g) => sum + session.tally[g], 0);

  return (
    <View style={styles.container} testID="review-summary">
      <Text style={styles.title} accessibilityRole="header">
        {t("review.summaryTitle")}
      </Text>
      <Text style={styles.text}>
        {t("review.reviewedCount", { count: reviewed })}
      </Text>
      <View style={styles.tally}>
        {GRADES.map((g) => (
          <View key={g} style={styles.tallyItem}>
            <Text style={styles.tallyNumber}>{session.tally[g]}</Text>
            <Text style={styles.muted}>{t(`review.grades.${g}`)}</Text>
          </View>
        ))}
      </View>

      {session.difficult.length > 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t("review.difficultTitle")}</Text>
          {session.difficult.map((c) => (
            <Text key={c.id} style={styles.text}>
              • {c.front}
            </Text>
          ))}
        </View>
      ) : null}

      {sync.nextDueAt ? (
        <Text style={styles.muted} testID="review-next-due">
          {t("review.nextDue", {
            time: sync.nextDueAt.toLocaleString(i18n.language, {
              day: "2-digit",
              month: "2-digit",
              hour: "2-digit",
              minute: "2-digit",
            }),
          })}
        </Text>
      ) : null}
      {sync.pending > 0 ? (
        <Text style={styles.offline} testID="review-pending">
          {t("review.pendingSync", { count: sync.pending })}
        </Text>
      ) : null}

      <Button label={t("review.done")} onPress={onDone} testID="review-done" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.lg },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  text: { color: colors.text, fontSize: fontSize.md },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  tally: { flexDirection: "row", gap: spacing.md },
  tallyItem: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    flex: 1,
    padding: spacing.md,
  },
  tallyNumber: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  section: { gap: spacing.xs },
  sectionTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "600",
  },
  offline: {
    backgroundColor: colors.background,
    borderRadius: radius.md,
    color: colors.textMuted,
    fontSize: fontSize.sm,
    padding: spacing.md,
  },
});
