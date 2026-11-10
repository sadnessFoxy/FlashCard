import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";

type Variant = "primary" | "secondary" | "danger";

interface Props {
  label: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: Variant;
  testID?: string;
}

const FILLED: Record<Variant, boolean> = {
  primary: true,
  secondary: false,
  danger: true,
};

export function Button({
  label,
  onPress,
  loading = false,
  disabled = false,
  variant = "primary",
  testID,
}: Props) {
  const inactive = disabled || loading;
  const filled = FILLED[variant];
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: inactive, busy: loading }}
      onPress={onPress}
      disabled={inactive}
      testID={testID}
      style={({ pressed }) => [
        styles.base,
        variant === "primary"
          ? styles.primary
          : variant === "danger"
            ? styles.danger
            : styles.secondary,
        pressed && styles.pressed,
        inactive && styles.inactive,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={filled ? colors.onPrimary : colors.primary} />
      ) : (
        <Text
          style={[
            styles.label,
            filled ? styles.labelFilled : styles.labelOutline,
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
  secondary: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
  },
  danger: { backgroundColor: colors.danger },
  pressed: { opacity: 0.85 },
  inactive: { opacity: 0.6 },
  label: { fontSize: fontSize.md, fontWeight: "600" },
  labelFilled: { color: colors.onPrimary },
  labelOutline: { color: colors.text },
});
