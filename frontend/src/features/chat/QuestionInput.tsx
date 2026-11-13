import { useTranslation } from "react-i18next";
import { StyleSheet, TextInput, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";

export const MAX_QUESTION_CHARS = 2000;

export function QuestionInput({
  value,
  onChange,
  onSend,
  busy,
}: {
  value: string;
  onChange: (text: string) => void;
  onSend: () => void;
  busy: boolean;
}) {
  const { t } = useTranslation();
  return (
    <View style={styles.row}>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={t("chat.placeholder")}
        placeholderTextColor={colors.textMuted}
        multiline
        maxLength={MAX_QUESTION_CHARS}
        editable={!busy}
        style={styles.input}
        accessibilityLabel={t("chat.placeholder")}
        testID="chat-input"
      />
      <Button
        label={t("chat.send")}
        onPress={onSend}
        loading={busy}
        disabled={busy || value.trim().length === 0}
        testID="chat-send"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  row: { alignItems: "flex-end", flexDirection: "row", gap: spacing.sm },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    color: colors.text,
    flex: 1,
    fontSize: fontSize.md,
    maxHeight: 140,
    minHeight: 46,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
});
