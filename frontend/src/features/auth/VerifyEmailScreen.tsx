import { useRouter } from "expo-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Pressable, ScrollView, StyleSheet, Text } from "react-native";

import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { confirmEmailVerification, sendEmailVerification } from "./api";
import { authErrorMessage } from "./errorMessage";
import { useAuthStore } from "./useAuthStore";

/** Screen 3: enter the emailed code; resend is rate limited by the server (U2). */
export function VerifyEmailScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const userUpdated = useAuthStore((s) => s.userUpdated);
  const [code, setCode] = useState("");
  const [message, setMessage] = useState<{
    text: string;
    error: boolean;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const back = () =>
    router.canGoBack() ? router.back() : router.replace("/spaces");

  async function confirm() {
    setBusy(true);
    setMessage(null);
    try {
      userUpdated(await confirmEmailVerification(code.trim()));
    } catch (e) {
      setMessage({ text: authErrorMessage(e, t), error: true });
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    setMessage(null);
    try {
      await sendEmailVerification();
      setMessage({ text: t("verify.resent"), error: false });
    } catch (e) {
      setMessage({ text: authErrorMessage(e, t), error: true });
    }
  }

  if (user?.email_verified) {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title} accessibilityRole="header">
          {t("verify.title")}
        </Text>
        <Text style={styles.notice} testID="verify-done">
          {t("verify.done")}
        </Text>
        <Button label={t("common.back")} onPress={back} />
      </ScrollView>
    );
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Pressable accessibilityRole="link" onPress={back}>
        <Text style={styles.link}>{t("common.back")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header">
        {t("verify.title")}
      </Text>
      <Text style={styles.text}>
        {t("verify.hint", { email: user?.email ?? "" })}
      </Text>
      <TextField
        label={t("forgot.code")}
        value={code}
        onChangeText={setCode}
        keyboardType="number-pad"
        maxLength={6}
        testID="verify-code"
      />
      <Button
        label={t("verify.confirm")}
        onPress={() => void confirm()}
        loading={busy}
        disabled={code.trim().length !== 6}
        testID="verify-submit"
      />
      <Pressable
        accessibilityRole="button"
        onPress={() => void resend()}
        testID="verify-resend"
      >
        <Text style={styles.link}>{t("verify.resend")}</Text>
      </Pressable>
      {message ? (
        <Text
          style={message.error ? styles.error : styles.muted}
          accessibilityRole={message.error ? "alert" : undefined}
          testID="verify-message"
        >
          {message.text}
        </Text>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    gap: spacing.md,
    maxWidth: 440,
    padding: spacing.xl,
    width: "100%",
  },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  text: { color: colors.text, fontSize: fontSize.md },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  notice: {
    backgroundColor: colors.background,
    borderRadius: radius.md,
    color: colors.text,
    fontSize: fontSize.md,
    padding: spacing.md,
  },
  error: { color: colors.danger, fontSize: fontSize.sm },
});
