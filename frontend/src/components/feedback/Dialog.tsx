import type { ReactNode } from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";

interface Props {
  visible: boolean;
  title: string;
  onDismiss: () => void;
  children: ReactNode;
  testID?: string;
}

// Cross-platform dialog: Alert.alert does nothing on web, Modal works everywhere.
export function Dialog({ visible, title, onDismiss, children, testID }: Props) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onDismiss}
    >
      <Pressable
        style={styles.backdrop}
        onPress={onDismiss}
        accessibilityRole="none"
      >
        {/* Stop presses inside the card from closing the dialog. */}
        <Pressable
          style={styles.card}
          onPress={() => undefined}
          testID={testID}
        >
          <Text style={styles.title} accessibilityRole="header">
            {title}
          </Text>
          <View style={styles.body}>{children}</View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    alignItems: "center",
    backgroundColor: "rgba(17, 24, 39, 0.45)",
    flex: 1,
    justifyContent: "center",
    padding: spacing.xl,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    gap: spacing.lg,
    maxWidth: 440,
    padding: spacing.xl,
    width: "100%",
  },
  title: { color: colors.text, fontSize: fontSize.lg, fontWeight: "700" },
  body: { gap: spacing.lg },
});
