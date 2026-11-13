import { useTranslation } from "react-i18next";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { CardSource } from "./api";
import { BACK_MAX, FRONT_MAX } from "./CardEditorDialog";
import { sourceLabel } from "./CardRow";

export interface DraftCard {
  key: string;
  front: string;
  back: string;
  source: CardSource;
  selected: boolean;
}

/** One AI-proposed card: the learner edits it and decides whether to keep it. */
export function SuggestionItem({
  draft,
  onChange,
}: {
  draft: DraftCard;
  onChange: (next: DraftCard) => void;
}) {
  const { t } = useTranslation();
  return (
    <View
      style={[styles.card, !draft.selected && styles.skipped]}
      testID={`suggestion-${draft.key}`}
    >
      <Pressable
        accessibilityRole="checkbox"
        accessibilityState={{ checked: draft.selected }}
        onPress={() => onChange({ ...draft, selected: !draft.selected })}
        style={styles.toggle}
        testID={`suggestion-toggle-${draft.key}`}
      >
        <Text style={styles.toggleText}>
          {draft.selected ? "☑" : "☐"}{" "}
          {t(draft.selected ? "cards.keep" : "cards.skip")}
        </Text>
      </Pressable>
      <TextInput
        value={draft.front}
        onChangeText={(front) => onChange({ ...draft, front })}
        maxLength={FRONT_MAX}
        multiline
        style={[styles.input, styles.front]}
        accessibilityLabel={t("cards.front")}
      />
      <TextInput
        value={draft.back}
        onChangeText={(back) => onChange({ ...draft, back })}
        maxLength={BACK_MAX}
        multiline
        style={styles.input}
        accessibilityLabel={t("cards.back")}
      />
      {draft.source ? (
        <Text style={styles.source}>{sourceLabel(draft.source, t)}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  skipped: { opacity: 0.5 },
  toggle: { alignSelf: "flex-start" },
  toggleText: {
    color: colors.primary,
    fontSize: fontSize.sm,
    fontWeight: "600",
  },
  input: {
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    color: colors.text,
    fontSize: fontSize.md,
    padding: spacing.sm,
  },
  front: { fontWeight: "600" },
  source: { color: colors.textMuted, fontSize: fontSize.sm },
});
