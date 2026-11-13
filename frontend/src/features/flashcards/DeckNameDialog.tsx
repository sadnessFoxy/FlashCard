import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { StyleSheet, View } from "react-native";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { spacing } from "../../theme/tokens";

const NAME_MAX = 100;

interface Props {
  visible: boolean;
  title: string;
  initialName?: string;
  onSubmit: (name: string) => Promise<unknown>;
  onClose: () => void;
}

export function DeckNameDialog({
  visible,
  title,
  initialName = "",
  onSubmit,
  onClose,
}: Props) {
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
    const trimmed = name.replace(/\s+/g, " ").trim();
    if (!trimmed) return setError(t("cards.errors.deckNameRequired"));
    if (trimmed.length > NAME_MAX)
      return setError(t("spaces.errors.nameTooLong", { max: NAME_MAX }));
    setSaving(true);
    try {
      await onSubmit(trimmed);
      onClose();
    } catch {
      setError(t("cards.errors.generic"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      visible={visible}
      title={title}
      onDismiss={onClose}
      testID="deck-name-dialog"
    >
      <TextField
        label={t("cards.deckName")}
        value={name}
        onChangeText={setName}
        placeholder={t("cards.deckNamePlaceholder")}
        autoFocus
        onSubmitEditing={() => void save()}
        error={error}
        testID="deck-name-input"
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
          testID="deck-name-save"
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
