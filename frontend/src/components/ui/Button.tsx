import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";

interface Props {
  label: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: "primary" | "secondary";
  testID?: string;
}

export function Button({
  label,
  onPress,
  loading = false,
  disabled = false,
  variant = "primary",
  testID,
}: Props) {
  const inactive = disabled || loading;
  const primary = variant === "primary";
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: inactive, busy: loading }}
      onPress={onPress}
      disabled={inactive}
      testID={testID}
      style={({ pressed }) => [
        styles.base,
        primary ? styles.primary : styles.secondary,
        pressed && primary && styles.primaryPressed,
        inactive && styles.inactive,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          color={primary ? colors.onPrimary : colors.primary}
        />
      ) : (
        <Text
          style={[
            styles.label,
            primary ? styles.labelPrimary : styles.labelSecondary,
          ]}
        >
          {label}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    alignItems: "center",
    borderRadius: radius.md,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.lg,
  },
  primary: { backgroundColor: colors.primary },
  primaryPressed: { backgroundColor: colors.primaryPressed },
  secondary: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
  },
  inactive: { opacity: 0.6 },
  label: { fontSize: fontSize.md, fontWeight: "600" },
  labelPrimary: { color: colors.onPrimary },
  labelSecondary: { color: colors.text },
});
