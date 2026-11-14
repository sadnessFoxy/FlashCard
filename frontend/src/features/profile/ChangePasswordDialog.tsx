import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { StyleSheet, Text, View } from "react-native";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize, spacing } from "../../theme/tokens";
import { useAuthStore } from "../auth/useAuthStore";
import { changePassword } from "./api";
import { profileErrorText } from "./profileErrors";

export function ChangePasswordDialog({
  visible,
  onClose,
}: {
  visible: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const userUpdated = useAuthStore((s) => s.userUpdated);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const toggle = { show: t("auth.showPassword"), hide: t("auth.hidePassword") };

  useEffect(() => {
    if (visible) {
      setCurrent("");
      setNext("");
      setConfirm("");
      setError(null);
    }
  }, [visible]);

  async function save() {
    if (next !== confirm) return setError(t("auth.errors.passwordMismatch"));
    setSaving(true);
    setError(null);
    try {
      userUpdated(await changePassword(current, next));
      onClose();
    } catch (e) {
      setError(profileErrorText(e, t));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      visible={visible}
      title={t("profile.changePassword")}
      onDismiss={onClose}
      testID="change-password-dialog"
    >
      <TextField
        label={t("profile.currentPassword")}
        value={current}
        onChangeText={setCurrent}
        autoComplete="current-password"
        secureToggle={toggle}
        testID="change-current"
      />
      <TextField
        label={t("forgot.newPassword")}
        value={next}
        onChangeText={setNext}
        autoComplete="new-password"
        secureToggle={toggle}
        testID="change-new"
      />
      <TextField
        label={t("auth.confirmPassword")}
        value={confirm}
        onChangeText={setConfirm}
        autoComplete="new-password"
        secureToggle={toggle}
        error={error}
        testID="change-confirm"
      />
      <Text style={styles.hint}>{t("profile.changePasswordHint")}</Text>
      <View style={styles.actions}>
        <Button
          label={t("common.cancel")}
          variant="secondary"
          onPress={onClose}
        />
        <Button
          label={t("common.save")}
          onPress={() => void save()}
          loading={saving}
          disabled={!current || !next}
          testID="change-save"
        />
      </View>
    </Dialog>
  );
}

const styles = StyleSheet.create({
  hint: { color: colors.textMuted, fontSize: fontSize.sm },
  actions: {
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "flex-end",
  },
});
