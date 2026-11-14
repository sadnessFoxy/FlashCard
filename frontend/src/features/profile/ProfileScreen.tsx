import { useRouter } from "expo-router";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { ChipGroup } from "../../components/ui/ChipGroup";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { Locale } from "../auth/api";
import { useAuthStore } from "../auth/useAuthStore";
import { useUsage } from "../chat/hooks";
import { updateLanguage } from "./api";
import { ChangePasswordDialog } from "./ChangePasswordDialog";
import { DeleteAccountDialog } from "./DeleteAccountDialog";

const LANGUAGES: { value: Locale; label: string }[] = [
  { value: "vi", label: "Tiếng Việt" },
  { value: "en", label: "English" },
];

/** Screen 4: account, language, today's AI allowance, password, sign out, delete (U4, U9, U10). */
export function ProfileScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const userUpdated = useAuthStore((s) => s.userUpdated);
  const logout = useAuthStore((s) => s.logout);
  const usage = useUsage();
  const [changingPassword, setChangingPassword] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [languageError, setLanguageError] = useState(false);

  async function chooseLanguage(locale: string) {
    setLanguageError(false);
    try {
      userUpdated(await updateLanguage(locale as Locale));
    } catch {
      setLanguageError(true);
    }
  }

  async function signOut() {
    setSigningOut(true);
    try {
      await logout();
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        {t("profile.title")}
      </Text>

      <Section title={t("profile.signedInAs")}>
        <Text style={styles.value} testID="profile-email">
          {user?.email}
        </Text>
        {user && !user.email_verified ? (
          <Pressable
            accessibilityRole="link"
            onPress={() => router.push("/spaces/verify-email")}
            testID="profile-verify"
          >
            <Text style={styles.link}>{t("profile.verifyEmail")}</Text>
          </Pressable>
        ) : (
          <Text style={styles.muted}>{t("profile.emailVerified")}</Text>
        )}
      </Section>

      <Section title={t("profile.language")}>
        <ChipGroup
          options={LANGUAGES}
          value={user?.locale ?? null}
          onChange={(value) => void chooseLanguage(value)}
          testID="profile-language"
        />
        {languageError ? (
          <Text style={styles.error}>{t("common.error")}</Text>
        ) : null}
      </Section>

      <Section title={t("profile.usageTitle")}>
        {usage.data ? (
          <>
            <Text style={styles.text} testID="profile-questions">
              {t("chat.quota", {
                remaining: usage.data.remaining,
                limit: usage.data.daily_limit,
              })}
            </Text>
            <Text style={styles.text} testID="profile-card-suggestions">
              {t("profile.cardSuggestionsLeft", {
                remaining: usage.data.card_suggestions.remaining,
                limit: usage.data.card_suggestions.daily_limit,
              })}
            </Text>
            <Text style={styles.muted}>{t("profile.usageResets")}</Text>
          </>
        ) : (
          <Text style={styles.muted}> </Text>
        )}
      </Section>

      <View style={styles.actions}>
        <Button
          label={t("profile.changePassword")}
          variant="secondary"
          onPress={() => setChangingPassword(true)}
          testID="profile-change-password"
        />
        <Button
          label={t("auth.logout")}
          variant="secondary"
          onPress={() => void signOut()}
          loading={signingOut}
          testID="profile-logout"
        />
        <Button
          label={t("profile.deleteAccount")}
          variant="danger"
          onPress={() => setDeleting(true)}
          testID="profile-delete"
        />
      </View>

      <ChangePasswordDialog
        visible={changingPassword}
        onClose={() => setChangingPassword(false)}
      />
      <DeleteAccountDialog
        visible={deleting}
        onClose={() => setDeleting(false)}
      />
    </ScrollView>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={styles.card}>
      <Text style={styles.label}>{title}</Text>
      {children}
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
    gap: spacing.sm,
    padding: spacing.lg,
  },
  label: { color: colors.textMuted, fontSize: fontSize.sm },
  value: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
  text: { color: colors.text, fontSize: fontSize.md },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  error: { color: colors.danger, fontSize: fontSize.sm },
  actions: { gap: spacing.sm },
});
