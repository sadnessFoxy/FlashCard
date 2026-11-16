import type { TextStyle, ViewStyle } from "react-native";

import { colors, fontSize, spacing } from "../../theme/tokens";

/** Styles shared by the admin screens (a plain object: StyleSheet lint rules are per file). */
export const adminStyles = {
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  section: { gap: spacing.sm },
  sectionTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "600",
  },
  strong: { color: colors.text, fontSize: fontSize.md, fontWeight: "600" },
  text: { color: colors.text, fontSize: fontSize.md },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  danger: { color: colors.danger, fontSize: fontSize.sm, fontWeight: "600" },
  actions: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
} satisfies Record<string, TextStyle | ViewStyle>;
