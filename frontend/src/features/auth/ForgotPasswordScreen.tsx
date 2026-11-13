import { useRouter } from "expo-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Pressable, ScrollView, StyleSheet, Text } from "react-native";

import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { confirmPasswordReset, requestPasswordReset } from "./api";
import { authErrorMessage } from "./errorMessage";

type Step = "email" | "code" | "done";
const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

/** Screen 2: ask for a code by email, then set a new password with it (U3). */
export function ForgotPasswordScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(task: () => Promise<void>) {
    setError(null);
    setBusy(true);
    try {
      await task();
    } catch (e) {
      setError(authErrorMessage(e, t));
    } finally {
      setBusy(false);
    }
  }

  const sendCode = () => {
    if (!EMAIL_PATTERN.test(email.trim())) {
      setError(t("auth.errors.invalidEmail"));
      return Promise.resolve();
    }
    return run(async () => {
      await requestPasswordReset(email.trim());
      setStep("code");
    });
  };

  const resetPassword = () =>
    run(async () => {
      if (password !== confirm) {
        setError(t("auth.errors.passwordMismatch"));
        return;
      }
      await confirmPasswordReset(email.trim(), code.trim(), password);
      setStep("done");
    });

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Pressable
        accessibilityRole="link"
        onPress={() => router.replace("/login")}
      >
        <Text style={styles.link}>{t("forgot.backToLogin")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header">
        {t("forgot.title")}
      </Text>

      {step === "email" ? (
        <>
          <Text style={styles.text}>{t("forgot.emailHint")}</Text>
          <TextField
            label={t("auth.email")}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            inputMode="email"
            testID="forgot-email"
          />
          <Button
            label={t("forgot.sendCode")}
            onPress={() => void sendCode()}
            loading={busy}
            testID="forgot-send"
          />
        </>
      ) : step === "code" ? (
        <>
          <Text style={styles.notice} testID="forgot-sent">
            {t("forgot.codeSent", { email: email.trim() })}
          </Text>
          <TextField
            label={t("forgot.code")}
            value={code}
            onChangeText={setCode}
            keyboardType="number-pad"
            maxLength={6}
            testID="forgot-code"
          />
          <TextField
            label={t("forgot.newPassword")}
            value={password}
            onChangeText={setPassword}
            autoComplete="new-password"
            secureToggle={{
              show: t("auth.showPassword"),
              hide: t("auth.hidePassword"),
            }}
            testID="forgot-password"
          />
          <Text style={styles.muted}>{t("auth.passwordHint")}</Text>
          <TextField
            label={t("auth.confirmPassword")}
            value={confirm}
            onChangeText={setConfirm}
            autoComplete="new-password"
            secureToggle={{
              show: t("auth.showPassword"),
              hide: t("auth.hidePassword"),
            }}
            testID="forgot-confirm"
          />
          <Button
            label={t("forgot.setPassword")}
            onPress={() => void resetPassword()}
            loading={busy}
            disabled={code.trim().length !== 6 || !password}
            testID="forgot-submit"
          />
          <Pressable accessibilityRole="button" onPress={() => void sendCode()}>
            <Text style={styles.link}>{t("forgot.resend")}</Text>
          </Pressable>
        </>
      ) : (
        <>
          <Text style={styles.notice} testID="forgot-done">
            {t("forgot.done")}
          </Text>
          <Button
            label={t("auth.login")}
            onPress={() => router.replace("/login")}
          />
        </>
      )}

      {error ? (
        <Text
          style={styles.error}
          accessibilityRole="alert"
          testID="forgot-error"
        >
          {error}
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
