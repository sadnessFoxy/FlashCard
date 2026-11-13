import { StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { fontSize } from "../../theme/tokens";
import type { DocumentStatus } from "./api";

const COLORS: Record<DocumentStatus, { fg: string; bg: string }> = {
  UPLOADED: { fg: "#1e40af", bg: "#dbeafe" },
  QUEUED: { fg: "#1e40af", bg: "#dbeafe" },
  PROCESSING: { fg: "#1e40af", bg: "#dbeafe" },
  READY: { fg: "#166534", bg: "#dcfce7" },
  FAILED: { fg: "#991b1b", bg: "#fee2e2" },
  PAUSED_QUOTA: { fg: "#92400e", bg: "#fef3c7" },
  DELETING: { fg: "#4b5563", bg: "#f3f4f6" },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const { t } = useTranslation();
  const c = COLORS[status];
  return (
    <View style={[styles.badge, { backgroundColor: c.bg }]}>
      <Text style={[styles.text, { color: c.fg }]}>
        {t(`documents.status.${status}`)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  text: { fontSize: fontSize.sm, fontWeight: "600" },
});
