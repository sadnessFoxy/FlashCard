import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, spacing } from "../../theme/tokens";
import type { Citation } from "./api";
import { pagesLabel } from "./labels";

// The highlight travels in the URL, so keep it short; the start is enough to match.
const HIGHLIGHT_CHARS = 300;

export function CitationDialog({
  citation,
  onClose,
}: {
  citation: Citation | null;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const router = useRouter();

  const openPage = (c: Citation, documentId: string) => {
    onClose();
    router.push({
      pathname: "/spaces/citation",
      params: {
        documentId,
        page: String(c.page_start),
        highlight: c.snippet.slice(0, HIGHLIGHT_CHARS),
      },
    });
  };

  return (
    <Dialog
      visible={citation !== null}
      title={citation ? `[${citation.index}] ${citation.document_name}` : ""}
      onDismiss={onClose}
      testID="citation-dialog"
    >
      {citation ? (
        <>
          <Text style={styles.muted}>
            {pagesLabel(citation, t)}
            {citation.document_id === null
              ? ` · ${t("chat.deletedDocument")}`
              : ""}
          </Text>
          <ScrollView style={styles.scroll}>
            <Text style={styles.snippet}>{citation.snippet}</Text>
          </ScrollView>
          <View style={styles.actions}>
            {citation.document_id !== null ? (
              <Button
                label={t("chat.viewPage")}
                onPress={() =>
                  openPage(citation, citation.document_id as string)
                }
                testID="citation-view-page"
              />
            ) : null}
            <Button
              label={t("common.close")}
              variant="secondary"
              onPress={onClose}
            />
          </View>
        </>
      ) : null}
    </Dialog>
  );
}

const styles = StyleSheet.create({
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  scroll: { maxHeight: 280 },
  snippet: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  actions: { gap: spacing.sm },
});
