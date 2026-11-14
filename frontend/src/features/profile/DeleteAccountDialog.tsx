import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { StyleSheet, Text } from "react-native";

import { ApiError } from "../../api/errors";
import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize } from "../../theme/tokens";
import { useAuthStore } from "../auth/useAuthStore";
import { deleteAccount } from "./api";
import { profileErrorText } from "./profileErrors";

/**
 * U9: the learner confirms with the password. A Google-only account has no password;
 * if the server says so, the dialog asks to retype the email instead.
 */
export function DeleteAccountDialog({
  visible,
  onClose,
}: {
  visible: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const sessionEnded = useAuthStore((s) => s.sessionEnded);
  const [byEmail, setByEmail] = useState(false);
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (visible) {
      setValue("");
      setError(null);
    }
  }, [visible]);

  async function confirm() {
    setDeleting(true);
    setError(null);
    try {
      await deleteAccount(
        byEmail ? { confirmEmail: value } : { password: value },
      );
      qc.clear(); // never keep the deleted account's data in memory
      sessionEnded();
    } catch (e) {
      if (e instanceof ApiError && e.code === "NO_PASSWORD") {
        setByEmail(true);
        setValue("");
        setError(t("profile.errors.retypeEmail"));
      } else {
        setError(profileErrorText(e, t));
      }
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Dialog
      visible={visible}
      title={t("profile.deleteTitle")}
      onDismiss={onClose}
      testID="delete-account-dialog"
    >
      <Text style={styles.warning}>{t("profile.deleteWarning")}</Text>
      <TextField
        label={t(byEmail ? "profile.confirmEmail" : "profile.currentPassword")}
        value={value}
        onChangeText={setValue}
        autoCapitalize="none"
        secureToggle={
          byEmail
            ? undefined
            : { show: t("auth.showPassword"), hide: t("auth.hidePassword") }
        }
        error={error}
        testID="delete-confirmation"
      />
      <Button
        label={t("profile.deleteConfirm")}
        variant="danger"
        onPress={() => void confirm()}
        loading={deleting}
        disabled={!value}
        testID="delete-account-confirm"
      />
      <Button
        label={t("common.cancel")}
        variant="secondary"
        onPress={onClose}
      />
    </Dialog>
  );
}

const styles = StyleSheet.create({
  warning: { color: colors.danger, fontSize: fontSize.md },
});
