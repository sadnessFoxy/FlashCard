import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useTranslation } from "react-i18next";

import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { login, register } from "./api";
import { authErrorMessage } from "./errorMessage";
import { useAuthStore } from "./useAuthStore";

type Mode = "login" | "register";

// Mirrors the server rules for instant feedback; the server stays the source of truth.
const MIN_PASSWORD_LENGTH = 8;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FieldErrors {
  email?: string;
  password?: string;
  confirm?: string;
}

export function LoginScreen() {
  const { t, i18n } = useTranslation();
  const signedIn = useAuthStore((s) => s.signedIn);
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const toggle = { show: t("auth.showPassword"), hide: t("auth.hidePassword") };

  function switchMode(next: Mode) {
    setMode(next);
    setFieldErrors({});
    setFormError(null);
    setConfirm("");
  }

  function validate(): FieldErrors {
    const errors: FieldErrors = {};
    if (!EMAIL_PATTERN.test(email.trim()))
      errors.email = t("auth.errors.invalidEmail");
    if (mode === "login" && password.length === 0)
      errors.password = t("auth.errors.passwordRequired");
    if (mode === "register") {
      if (password.length < MIN_PASSWORD_LENGTH) {
        errors.password = t("auth.errors.weakPassword.too_short");
      }
      if (confirm !== password)
        errors.confirm = t("auth.errors.passwordMismatch");
    }
    return errors;
  }

  async function submit() {
    const errors = validate();
    setFieldErrors(errors);
    setFormError(null);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      const credentials = { email: email.trim(), password };
      const user =
        mode === "login"
          ? await login(credentials)
          : await register(credentials, i18n.language === "en" ? "en" : "vi");
      signedIn(user);
    } catch (error) {
      setFormError(authErrorMessage(error, t));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      style={styles.flex}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title} accessibilityRole="header">
          {t("common.appName")}
        </Text>
        <Text style={styles.subtitle}>{t("auth.tagline")}</Text>

        <View style={styles.tabs} accessibilityRole="tablist">
          {(["login", "register"] as const).map((m) => (
            <Pressable
              key={m}
              accessibilityRole="tab"
              accessibilityState={{ selected: mode === m }}
              onPress={() => switchMode(m)}
              style={[styles.tab, mode === m && styles.tabActive]}
              testID={`auth-tab-${m}`}
            >
              <Text
                style={[styles.tabText, mode === m && styles.tabTextActive]}
              >
                {t(m === "login" ? "auth.login" : "auth.register")}
              </Text>
            </Pressable>
          ))}
        </View>

        <View style={styles.form}>
          <TextField
            label={t("auth.email")}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            autoComplete="email"
            keyboardType="email-address"
            inputMode="email"
            error={fieldErrors.email}
            testID="auth-email"
          />
          <TextField
            label={t("auth.password")}
            value={password}
            onChangeText={setPassword}
            autoComplete={
              mode === "login" ? "current-password" : "new-password"
            }
            secureToggle={toggle}
            error={fieldErrors.password}
            testID="auth-password"
          />
          {mode === "register" && (
            <TextField
              label={t("auth.confirmPassword")}
              value={confirm}
              onChangeText={setConfirm}
              autoComplete="new-password"
              secureToggle={toggle}
              error={fieldErrors.confirm}
              testID="auth-confirm"
            />
          )}
          {mode === "register" && (
            <Text style={styles.hint}>{t("auth.passwordHint")}</Text>
          )}

          {formError && (
            <View style={styles.formError} testID="auth-form-error">
              <Text style={styles.formErrorText}>{formError}</Text>
            </View>
          )}

          <Button
            label={t(mode === "login" ? "auth.login" : "auth.createAccount")}
            onPress={() => void submit()}
            loading={submitting}
            testID="auth-submit"
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { backgroundColor: colors.background, flex: 1 },
  container: {
    alignSelf: "center",
    gap: spacing.lg,
    maxWidth: 420,
    padding: spacing.xl,
    paddingTop: spacing.xxl * 2,
    width: "100%",
  },
  title: {
    color: colors.text,
    fontSize: fontSize.xl,
    fontWeight: "700",
    textAlign: "center",
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: fontSize.md,
    textAlign: "center",
  },
  tabs: {
    backgroundColor: colors.border,
    borderRadius: radius.md,
    flexDirection: "row",
    padding: 3,
  },
  tab: {
    alignItems: "center",
    borderRadius: radius.sm,
    flex: 1,
    paddingVertical: spacing.sm,
  },
  tabActive: { backgroundColor: colors.surface },
  tabText: {
    color: colors.textMuted,
    fontSize: fontSize.md,
    fontWeight: "600",
  },
  tabTextActive: { color: colors.text },
  form: { gap: spacing.lg },
  hint: { color: colors.textMuted, fontSize: fontSize.sm },
  formError: {
    backgroundColor: colors.dangerBg,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  formErrorText: { color: colors.danger, fontSize: fontSize.md },
});
