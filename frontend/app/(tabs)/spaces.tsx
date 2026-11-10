import { StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { colors, fontSize, spacing } from "../../src/theme/tokens";

// Placeholder until F4b (spaces).
export default function Spaces() {
  const { t } = useTranslation();
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        {t("tabs.spaces")}
      </Text>
      <Text style={styles.text}>{t("spaces.comingSoon")}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.md, padding: spacing.xl },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  text: { color: colors.textMuted, fontSize: fontSize.md },
});
