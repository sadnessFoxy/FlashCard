import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { StyleSheet, Text } from "react-native";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize } from "../../theme/tokens";

/** Confirm an admin action; `needsReason` asks for a reason that goes to the audit log. */
export function ReasonDialog({
  visible,
  title,
  message,
  confirmLabel,
  needsReason,
  busy,
  error,
  onConfirm,
  onClose,
}: {
  visible: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  needsReason: boolean;
  busy: boolean;
  error: string | null;
  onConfirm: (reason: string) => void;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const [reason, setReason] = useState("");
  useEffect(() => {
    if (visible) setReason("");
  }, [visible]);

  return (
    <Dialog
      visible={visible}
      title={title}
      onDismiss={onClose}
      testID="admin-confirm"
    >
      <Text style={styles.message}>{message}</Text>
      {needsReason ? (
        <TextField
          label={t("admin.reason")}
          value={reason}
          onChangeText={setReason}
          maxLength={500}
          testID="admin-reason"
        />
      ) : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <Button
        label={confirmLabel}
        variant="danger"
        onPress={() => onConfirm(reason.trim())}
        loading={busy}
        disabled={needsReason && !reason.trim()}
        testID="admin-confirm-ok"
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
  message: { color: colors.text, fontSize: fontSize.md },
  error: { color: colors.danger, fontSize: fontSize.sm },
});
