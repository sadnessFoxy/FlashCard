import { Pressable, ScrollView, StyleSheet, Text } from "react-native";

import { colors, fontSize, spacing } from "../../theme/tokens";

export interface ChipOption {
  value: string;
  label: string;
}

/** Single-choice chips in a horizontal row. */
export function ChipGroup({
  options,
  value,
  onChange,
  testID,
}: {
  options: ChipOption[];
  value: string | null;
  onChange: (value: string) => void;
  testID?: string;
}) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}
    >
      {options.map((o) => {
        const on = o.value === value;
        return (
          <Pressable
            key={o.value}
            accessibilityRole="radio"
            accessibilityState={{ selected: on }}
            onPress={() => onChange(o.value)}
            style={[styles.chip, on && styles.chipOn]}
            testID={testID ? `${testID}-${o.value}` : undefined}
          >
            <Text style={[styles.text, on && styles.textOn]} numberOfLines={1}>
              {o.label}
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
    maxWidth: 240,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  text: { color: colors.text, fontSize: fontSize.sm },
  textOn: { color: colors.onPrimary },
});
