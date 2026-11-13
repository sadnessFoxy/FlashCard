import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { Pressable, StyleSheet, Text } from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { useAuthStore } from "./useAuthStore";

/** Reminds unverified users; uploads need a verified email. Renders nothing otherwise. */
export function VerifyEmailBanner() {
  const { t } = useTranslation();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  if (!user || user.email_verified) return null;
  return (
    <Pressable
      accessibilityRole="link"
      onPress={() => router.push("/spaces/verify-email")}
      style={styles.banner}
      testID="verify-banner"
    >
      <Text style={styles.text}>{t("verify.banner")}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.highlight,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  text: { color: colors.text, fontSize: fontSize.sm, fontWeight: "600" },
});
