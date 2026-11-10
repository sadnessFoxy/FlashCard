import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize, spacing } from "../../theme/tokens";
import { apiNameError, localNameError, normalizeSpaceName } from "./nameError";

interface NameDialogProps {
  visible: boolean;
  mode: "create" | "rename";
  initialName?: string;
  onSubmit: (name: string) => Promise<unknown>;
  onClose: () => void;
}

export function SpaceNameDialog({
  visible,
  mode,
  initialName = "",
  onSubmit,
  onClose,
}: NameDialogProps) {
  const { t } = useTranslation();
  const [name, setName] = useState(initialName);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (visible) {
      setName(initialName);
      setError(null);
    }
  }, [visible, initialName]);

  async function save() {
    const local = localNameError(name, t);
    if (local) {
      setError(local);
      return;
    }
    setSaving(true);
    try {
      await onSubmit(normalizeSpaceName(name));
      onClose();
    } catch (e) {
      setError(apiNameError(e, t));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      visible={visible}
      title={t(mode === "create" ? "spaces.createTitle" : "spaces.renameTitle")}
      onDismiss={onClose}
      testID="space-name-dialog"
    >
      <TextField
        label={t("spaces.nameLabel")}
        value={name}
        onChangeText={setName}
        placeholder={t("spaces.namePlaceholder")}
        autoFocus
        onSubmitEditing={() => void save()}
        error={error}
        testID="space-name-input"
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
          testID="space-name-save"
        />
      </View>
    </Dialog>
  );
}

interface DeleteDialogProps {
  spaceName: string | null;
  onConfirm: () => Promise<unknown>;
  onClose: () => void;
}

export function DeleteSpaceDialog({
  spaceName,
  onConfirm,
  onClose,
}: DeleteDialogProps) {
  const { t } = useTranslation();
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setError(null), [spaceName]);

  async function confirm() {
    setDeleting(true);
    try {
      await onConfirm();
      onClose();
    } catch (e) {
      setError(apiNameError(e, t));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Dialog
      visible={spaceName !== null}
      title={t("spaces.deleteTitle", { name: spaceName ?? "" })}
      onDismiss={onClose}
      testID="space-delete-dialog"
    >
      <Text style={styles.warning}>{t("spaces.deleteWarning")}</Text>
      {error && <Text style={styles.error}>{error}</Text>}
      <View style={styles.actions}>
        <Button
          label={t("common.cancel")}
          variant="secondary"
          onPress={onClose}
        />
        <Button
          label={t("common.delete")}
          variant="danger"
          onPress={() => void confirm()}
          loading={deleting}
          testID="space-delete-confirm"
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
  warning: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  error: { color: colors.danger, fontSize: fontSize.sm },
});
