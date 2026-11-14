import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
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
import { useUsage } from "../chat/hooks";
import { summaryErrorText } from "./errors";
import { useSections, useSummarize } from "./hooks";
import { SectionCard } from "./SectionCard";

/** Screen 8: chapters of a document; summaries are made on request and kept (U15). */
export function SummaryScreen({ documentId }: { documentId: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const sections = useSections(documentId);
  const summarize = useSummarize(documentId);
  const usage = useUsage();
  const back = () =>
    router.canGoBack() ? router.back() : router.replace("/spaces");

  if (sections.isPending) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  if (sections.isError) {
    return (
      <View style={styles.center} testID="summary-error">
        <Text style={styles.muted}>{summaryErrorText(sections.error, t)}</Text>
        <Button label={t("common.back")} variant="secondary" onPress={back} />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable accessibilityRole="link" onPress={back}>
        <Text style={styles.link}>{t("common.back")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header">
        {t("summaries.title")}
      </Text>
      <Text style={styles.muted}>{sections.data.filename}</Text>
      {usage.data ? (
        <Text style={styles.muted} testID="summary-quota">
          {t("summaries.quota", {
            remaining: usage.data.summaries.remaining,
            limit: usage.data.summaries.daily_limit,
          })}
        </Text>
      ) : null}
      {summarize.isError ? (
        <Text
          style={styles.error}
          accessibilityRole="alert"
          testID="summary-make-error"
        >
          {summaryErrorText(summarize.error, t)}
        </Text>
      ) : null}

      {sections.data.items.map((section) => (
        <SectionCard
          key={section.id}
          documentId={documentId}
          section={section}
          busy={summarize.isPending && summarize.variables === section.id}
          onSummarize={() => summarize.mutate(section.id)}
        />
      ))}
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
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  error: {
    backgroundColor: colors.dangerBg,
    borderRadius: radius.md,
    color: colors.danger,
    fontSize: fontSize.sm,
    padding: spacing.md,
  },
});
