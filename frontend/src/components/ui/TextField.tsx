import { useState } from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";

interface Props extends Omit<TextInputProps, "style"> {
  label: string;
  error?: string | null;
  /** Adds a show/hide toggle; labels come from the caller (i18n). */
  secureToggle?: { show: string; hide: string };
}

export function TextField({
  label,
  error,
  secureToggle,
  testID,
  ...input
}: Props) {
  const [revealed, setRevealed] = useState(false);
  const secure = Boolean(secureToggle) && !revealed;
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <View style={[styles.inputRow, error ? styles.inputRowError : null]}>
        <TextInput
          {...input}
          accessibilityLabel={label}
          secureTextEntry={secure}
          placeholderTextColor={colors.textMuted}
          style={styles.input}
          testID={testID}
        />
        {secureToggle && (
          <Pressable
            accessibilityRole="button"
            onPress={() => setRevealed((v) => !v)}
            hitSlop={8}
            testID={testID ? `${testID}-toggle` : undefined}
          >
            <Text style={styles.toggle}>
              {revealed ? secureToggle.hide : secureToggle.show}
            </Text>
          </Pressable>
        )}
      </View>
      {error ? (
        <Text style={styles.error} accessibilityLiveRegion="polite">
          {error}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  label: { color: colors.text, fontSize: fontSize.sm, fontWeight: "600" },
  inputRow: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    flexDirection: "row",
    paddingHorizontal: spacing.md,
  },
  inputRowError: { borderColor: colors.danger },
  input: { color: colors.text, flex: 1, fontSize: fontSize.md, minHeight: 46 },
  toggle: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  error: { color: colors.danger, fontSize: fontSize.sm },
});
