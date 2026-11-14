import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { Section } from "./api";

export function sectionTitle(
  section: Section,
  t: ReturnType<typeof useTranslation>["t"],
) {
  const pages =
    section.page_start === section.page_end
      ? t("chat.page", { page: section.page_start })
      : t("chat.pages", { start: section.page_start, end: section.page_end });
  return section.title ? `${section.title} · ${pages}` : pages;
}

/** One chapter: its summary with page links, or a button to make it. */
export function SectionCard({
  documentId,
  section,
  busy,
  onSummarize,
}: {
  documentId: string;
  section: Section;
  busy: boolean;
  onSummarize: () => void;
}) {
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <View style={styles.card} testID={`section-${section.id}`}>
      <Text style={styles.title}>{sectionTitle(section, t)}</Text>
      {section.summary ? (
        section.summary.points.map((point, i) => (
          <View key={i} style={styles.point}>
            <Text style={styles.text}>• {point.text}</Text>
            {point.page ? (
              <Pressable
                accessibilityRole="link"
                onPress={() =>
                  router.push({
                    pathname: "/spaces/citation",
                    params: {
                      documentId,
                      page: String(point.page),
                      highlight: point.text,
                    },
                  })
                }
              >
                <Text style={styles.link}>
                  {t("chat.page", { page: point.page })}
                </Text>
              </Pressable>
            ) : null}
          </View>
        ))
      ) : (
        <Button
          label={t("summaries.make")}
          variant="secondary"
          onPress={onSummarize}
          loading={busy}
          testID={`section-summarize-${section.id}`}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.md,
  },
  title: { color: colors.text, fontSize: fontSize.md, fontWeight: "600" },
  point: { gap: 2 },
  text: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  link: { color: colors.primary, fontSize: fontSize.sm },
});
