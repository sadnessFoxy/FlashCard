import { Redirect } from "expo-router";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Platform, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, spacing } from "../../theme/tokens";
import { useAuthStore } from "../auth/useAuthStore";

/**
 * The admin console is web only and for admins. Hiding it here is only convenience:
 * the backend checks the role on every admin call (R13).
 */
export function AdminGate({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);

  if (status === "signedOut") return <Redirect href="/login" />;
  if (Platform.OS !== "web") return <Notice text={t("admin.webOnly")} />;
  if (status !== "signedIn" || !user) return null;
  if (user.role !== "admin") return <Notice text={t("admin.notAdmin")} />;
  return <>{children}</>;
}

function Notice({ text }: { text: string }) {
  return (
    <View style={styles.center} testID="admin-gate-notice">
      <Text style={styles.text}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    alignItems: "center",
    flex: 1,
    justifyContent: "center",
    padding: spacing.xl,
  },
  text: { color: colors.text, fontSize: fontSize.md, textAlign: "center" },
});
