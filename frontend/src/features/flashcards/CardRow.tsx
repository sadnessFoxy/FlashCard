import { useTranslation } from "react-i18next";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { CardSource, Flashcard } from "./api";

export function sourceLabel(
  source: NonNullable<CardSource>,
  t: ReturnType<typeof useTranslation>["t"],
): string {
  const page = source.page ? ` · ${t("chat.page", { page: source.page })}` : "";
  const deleted =
    source.document_id === null ? ` · ${t("chat.deletedDocument")}` : "";
  return `${source.document_name}${page}${deleted}`;
}

interface Props {
  card: Flashcard;
  onEdit: () => void;
  onDelete: () => void;
  onOpenSource: () => void;
}

export function CardRow({ card, onEdit, onDelete, onOpenSource }: Props) {
  const { t } = useTranslation();
  const source = card.source;
  return (
    <View style={styles.row} testID={`card-${card.id}`}>
      <Text style={styles.front}>{card.front}</Text>
      <Text style={styles.back}>{card.back}</Text>
      {source ? (
        <Pressable
          accessibilityRole="link"
          onPress={onOpenSource}
          disabled={source.document_id === null || !source.page}
        >
          <Text style={styles.source}>{sourceLabel(source, t)}</Text>
        </Pressable>
      ) : null}
      <View style={styles.actions}>
        <Pressable
          accessibilityRole="button"
          onPress={onEdit}
          testID={`card-edit-${card.id}`}
        >
          <Text style={styles.link}>{t("cards.edit")}</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={onDelete}
          testID={`card-delete-${card.id}`}
        >
          <Text style={styles.danger}>{t("common.delete")}</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  front: { color: colors.text, fontSize: fontSize.md, fontWeight: "600" },
  back: { color: colors.text, fontSize: fontSize.md },
  source: { color: colors.primary, fontSize: fontSize.sm },
  actions: {
    flexDirection: "row",
    gap: spacing.lg,
    justifyContent: "flex-end",
  },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  danger: { color: colors.danger, fontSize: fontSize.sm, fontWeight: "600" },
});
