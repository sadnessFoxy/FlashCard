import { useRouter, type Href } from "expo-router";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";

const NAV: { href: Href; key: string }[] = [
  { href: "/admin", key: "overview" },
  { href: "/admin/users", key: "users" },
  { href: "/admin/documents", key: "documents" },
  { href: "/admin/settings", key: "settings" },
  { href: "/admin/audit", key: "audit" },
];

/** Shared frame of the admin screens: navigation, title, loading and error states. */
export function AdminPage({
  title,
  loading,
  error,
  children,
}: {
  title: string;
  loading?: boolean;
  error?: boolean;
  children?: ReactNode;
}) {
  const { t } = useTranslation();
  const router = useRouter();
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.nav} accessibilityRole="tablist">
        {NAV.map((item) => (
          <Pressable
            key={item.key}
            accessibilityRole="link"
            onPress={() => router.push(item.href)}
            testID={`admin-nav-${item.key}`}
          >
            <Text style={styles.navText}>{t(`admin.nav.${item.key}`)}</Text>
          </Pressable>
        ))}
        <Pressable
          accessibilityRole="link"
          onPress={() => router.replace("/spaces")}
        >
          <Text style={styles.navMuted}>{t("admin.nav.exit")}</Text>
        </Pressable>
      </View>
      <Text style={styles.title} accessibilityRole="header">
        {title}
      </Text>
      {loading ? (
        <ActivityIndicator color={colors.primary} />
      ) : error ? (
        <Text style={styles.error}>{t("admin.loadError")}</Text>
      ) : (
        children
      )}
    </ScrollView>
  );
}

export function Stat({
  label,
  value,
  alert = false,
}: {
  label: string;
  value: string | number;
  alert?: boolean;
}) {
  return (
    <View style={[styles.stat, alert && styles.statAlert]}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export function Row({
  children,
  onPress,
  testID,
}: {
  children: ReactNode;
  onPress?: () => void;
  testID?: string;
}) {
  return (
    <Pressable
      style={styles.row}
      onPress={onPress}
      disabled={!onPress}
      accessibilityRole={onPress ? "button" : undefined}
      testID={testID}
    >
      {children}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    gap: spacing.lg,
    maxWidth: 1100,
    padding: spacing.xl,
    width: "100%",
  },
  nav: { flexDirection: "row", flexWrap: "wrap", gap: spacing.lg },
  navText: { color: colors.primary, fontSize: fontSize.md, fontWeight: "600" },
  navMuted: { color: colors.textMuted, fontSize: fontSize.md },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  error: { color: colors.danger, fontSize: fontSize.md },
  stat: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    minWidth: 170,
    padding: spacing.md,
  },
  statAlert: { backgroundColor: colors.dangerBg, borderColor: colors.danger },
  statValue: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  statLabel: { color: colors.textMuted, fontSize: fontSize.sm },
  row: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
});
