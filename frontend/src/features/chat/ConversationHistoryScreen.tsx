import { useRouter } from "expo-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { Conversation } from "./api";
import { useConversations, useDeleteConversation } from "./hooks";

/** Screen 11: the conversations of a space; open one again or delete it. */
export function ConversationHistoryScreen({ spaceId }: { spaceId: string }) {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const conversations = useConversations(spaceId);
  const remove = useDeleteConversation(spaceId);
  const [deleting, setDeleting] = useState<Conversation | null>(null);

  const backToChat = (conversationId?: string) =>
    router.replace({
      pathname: "/spaces/[id]",
      params: conversationId
        ? { id: spaceId, tab: "chat", conversation: conversationId }
        : { id: spaceId, tab: "chat" },
    });

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString(i18n.language, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <View style={styles.container}>
      <Pressable accessibilityRole="link" onPress={() => backToChat()}>
        <Text style={styles.link}>{t("history.back")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header">
        {t("history.title")}
      </Text>

      {conversations.isPending ? (
        <ActivityIndicator color={colors.primary} />
      ) : conversations.isError ? (
        <Text style={styles.muted}>{t("history.loadError")}</Text>
      ) : conversations.data.items.length === 0 ? (
        <Text style={styles.muted} testID="history-empty">
          {t("history.empty")}
        </Text>
      ) : (
        <FlatList
          data={conversations.data.items}
          keyExtractor={(c) => c.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <View style={styles.row}>
              <Pressable
                style={styles.rowMain}
                accessibilityRole="button"
                onPress={() => backToChat(item.id)}
                testID={`history-open-${item.id}`}
              >
                <Text style={styles.rowTitle} numberOfLines={2}>
                  {item.title ?? t("history.untitled")}
                </Text>
                <Text style={styles.muted}>{formatDate(item.updated_at)}</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={t("common.delete")}
                onPress={() => setDeleting(item)}
                testID={`history-delete-${item.id}`}
              >
                <Text style={styles.danger}>{t("common.delete")}</Text>
              </Pressable>
            </View>
          )}
        />
      )}

      <Dialog
        visible={deleting !== null}
        title={t("history.deleteTitle")}
        onDismiss={() => setDeleting(null)}
        testID="history-delete-dialog"
      >
        <Text style={styles.body}>{t("history.deleteWarning")}</Text>
        <Button
          label={t("common.delete")}
          variant="danger"
          loading={remove.isPending}
          onPress={() => {
            if (!deleting) return;
            remove.mutate(deleting.id, { onSettled: () => setDeleting(null) });
          }}
          testID="history-delete-confirm"
        />
        <Button
          label={t("common.cancel")}
          variant="secondary"
          onPress={() => setDeleting(null)}
        />
      </Dialog>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    flex: 1,
    gap: spacing.md,
    maxWidth: 720,
    padding: spacing.xl,
    width: "100%",
  },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  body: { color: colors.text, fontSize: fontSize.md },
  danger: { color: colors.danger, fontSize: fontSize.sm, fontWeight: "600" },
  list: { gap: spacing.sm },
  row: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    padding: spacing.md,
  },
  rowMain: { flex: 1, gap: spacing.xs },
  rowTitle: { color: colors.text, fontSize: fontSize.md, fontWeight: "600" },
});
