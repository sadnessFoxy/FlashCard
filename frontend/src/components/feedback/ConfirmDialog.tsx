import { StyleSheet, Text } from "react-native";

import { colors, fontSize } from "../../theme/tokens";
import { Button } from "../ui/Button";
import { Dialog } from "./Dialog";

interface Props {
  visible: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
  destructive?: boolean;
  testID?: string;
}

/** Yes/no question; labels come from the caller (i18n). */
export function ConfirmDialog({
  visible,
  title,
  message,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
  busy = false,
  destructive = true,
  testID,
}: Props) {
  return (
    <Dialog
      visible={visible}
      title={title}
      onDismiss={onCancel}
      testID={testID}
    >
      <Text style={styles.message}>{message}</Text>
      <Button
        label={confirmLabel}
        variant={destructive ? "danger" : "primary"}
        loading={busy}
        onPress={onConfirm}
        testID={testID ? `${testID}-confirm` : undefined}
      />
      <Button label={cancelLabel} variant="secondary" onPress={onCancel} />
    </Dialog>
  );
}

const styles = StyleSheet.create({
  message: { color: colors.text, fontSize: fontSize.md },
});
