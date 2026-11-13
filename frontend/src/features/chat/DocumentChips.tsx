import { Pressable, ScrollView, StyleSheet, Text } from "react-native";

import { colors, fontSize, spacing } from "../../theme/tokens";
import type { DocumentItem } from "../documents/api";

/** Toggle which READY documents a question is asked against. */
export function DocumentChips({
  documents,
  excluded,
  onToggle,
}: {
  documents: DocumentItem[];
  excluded: ReadonlySet<string>;
  onToggle: (id: string) => void;
}) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}
    >
      {documents.map((d) => {
        const on = !excluded.has(d.id);
        return (
          <Pressable
            key={d.id}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: on }}
            onPress={() => onToggle(d.id)}
            style={[styles.chip, on && styles.chipOn]}
            testID={`chat-doc-${d.id}`}
          >
            <Text style={[styles.text, on && styles.textOn]} numberOfLines={1}>
              {d.filename}
            </Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.sm },
  chip: {
    borderColor: colors.border,
    borderRadius: 999,
    borderWidth: 1,
    maxWidth: 220,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  text: { color: colors.text, fontSize: fontSize.sm },
  textOn: { color: colors.onPrimary },
});
