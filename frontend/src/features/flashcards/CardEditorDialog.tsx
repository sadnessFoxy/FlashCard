import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { StyleSheet, View } from "react-native";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { spacing } from "../../theme/tokens";

export const FRONT_MAX = 500;
export const BACK_MAX = 2000;

interface Props {
  visible: boolean;
  title: string;
  initial?: { front: string; back: string };
  /** Throw to keep the dialog open; the message is shown under the fields. */
  onSave: (front: string, back: string) => Promise<unknown>;
  onClose: () => void;
  errorText?: (error: unknown) => string;
}

/** Front/back form shared by "add card" and "edit card". */
export function CardEditorDialog({
  visible,
  title,
  initial,
  onSave,
  onClose,
  errorText,
}: Props) {
  const { t } = useTranslation();
  const [front, setFront] = useState("");
  const [back, setBack] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (visible) {
      setFront(initial?.front ?? "");
      setBack(initial?.back ?? "");
      setError(null);
    }
  }, [visible, initial]);

  async function save() {
    if (!front.trim() || !back.trim()) {
      setError(t("cards.errors.required"));
      return;
    }
    setSaving(true);
    try {
      await onSave(front.trim(), back.trim());
      onClose();
    } catch (e) {
      setError(errorText ? errorText(e) : t("cards.errors.generic"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      visible={visible}
      title={title}
      onDismiss={onClose}
      testID="card-editor"
    >
      <TextField
        label={t("cards.front")}
        value={front}
        onChangeText={setFront}
        maxLength={FRONT_MAX}
        multiline
        testID="card-front"
      />
      <TextField
        label={t("cards.back")}
        value={back}
        onChangeText={setBack}
        maxLength={BACK_MAX}
        multiline
        error={error}
        testID="card-back"
      />
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
          testID="card-save"
        />
      </View>
    </Dialog>
  );
}

const styles = StyleSheet.create({
  actions: {
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "flex-end",
  },
});
