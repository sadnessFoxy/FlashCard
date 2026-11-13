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

import { ApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { isHighlighted } from "./highlight";
import { useDocumentPage } from "./hooks";

interface Props {
  documentId: string;
  page: number;
  /** Start of the cited snippet; matching paragraphs are highlighted on the cited page. */
  highlight: string;
}

/** Screen 10: the cited page as text, with the cited passage highlighted. */
export function CitationPageScreen({ documentId, page, highlight }: Props) {
  const { t } = useTranslation();
  const router = useRouter();
  const [current, setCurrent] = useState(page);
  const query = useDocumentPage(documentId, current);
  const goBack = () =>
    router.canGoBack() ? router.back() : router.replace("/spaces");

  if (query.isPending) {
    return (
      <View style={styles.center} testID="citation-page-loading">
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (query.isError) {
    const code = query.error instanceof ApiError ? query.error.code : null;
    return (
      <View style={styles.center} testID="citation-page-error">
        <Text style={styles.muted}>
          {t(
            code === "NOT_FOUND"
              ? "citationPage.notFound"
              : code === "DOCUMENT_NOT_READY"
                ? "citationPage.notReady"
                : "citationPage.loadError",
          )}
        </Text>
        <Button label={t("common.back")} variant="secondary" onPress={goBack} />
      </View>
    );
  }

  const data = query.data;
  const onCitedPage = current === page;

  return (
    <View style={styles.container}>
      <Pressable accessibilityRole="link" onPress={goBack}>
        <Text style={styles.link}>{t("common.back")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header">
        {data.filename}
      </Text>
      <Text style={styles.muted} testID="citation-page-number">
        {t("citationPage.pageOf", { page: data.page, total: data.page_count })}
      </Text>

      <ScrollView
        style={styles.page}
        contentContainerStyle={styles.pageContent}
      >
        {data.paragraphs.length === 0 ? (
          <Text style={styles.muted}>{t("citationPage.noText")}</Text>
        ) : (
          data.paragraphs.map((paragraph, i) => {
            const marked = onCitedPage && isHighlighted(paragraph, highlight);
            return (
              <Text
                key={i}
                style={[styles.paragraph, marked && styles.marked]}
                testID={marked ? "citation-highlight" : undefined}
              >
                {paragraph}
              </Text>
            );
          })
        )}
      </ScrollView>

      <View style={styles.pager}>
        <Button
          label={t("citationPage.previous")}
          variant="secondary"
          disabled={current <= 1}
          onPress={() => setCurrent((n) => n - 1)}
          testID="citation-page-previous"
        />
        <Button
          label={t("citationPage.next")}
          variant="secondary"
          disabled={current >= data.page_count}
          onPress={() => setCurrent((n) => n + 1)}
          testID="citation-page-next"
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    flex: 1,
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
  page: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    flex: 1,
  },
  pageContent: { gap: spacing.md, padding: spacing.lg },
  paragraph: { color: colors.text, fontSize: fontSize.md, lineHeight: 24 },
  marked: {
    backgroundColor: colors.highlight,
    borderRadius: radius.sm,
    padding: spacing.xs,
  },
  pager: {
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between",
  },
});
