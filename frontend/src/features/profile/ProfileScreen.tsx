import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { useAuthStore } from "../auth/useAuthStore";

// F2 scope: who is signed in + sign out. Language, quota, password, delete account come in F15.
export function ProfileScreen() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [busy, setBusy] = useState(false);

  async function onLogout() {
    setBusy(true);
    try {
      await logout();
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        {t("profile.title")}
      </Text>
      <View style={styles.card}>
        <Text style={styles.label}>{t("profile.signedInAs")}</Text>
        <Text style={styles.value} testID="profile-email">
          {user?.email}
        </Text>
      </View>
      <Button
        label={t("auth.logout")}
        variant="secondary"
        onPress={() => void onLogout()}
        loading={busy}
        testID="profile-logout"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    gap: spacing.lg,
    maxWidth: 640,
    padding: spacing.xl,
    width: "100%",
  },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.lg,
  },
  label: { color: colors.textMuted, fontSize: fontSize.sm },
  value: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
});
