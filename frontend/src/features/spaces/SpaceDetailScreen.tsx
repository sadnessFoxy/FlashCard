import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useTranslation } from "react-i18next";

import { ApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { ChatTab } from "../chat/ChatTab";
import { DocumentsTab } from "../documents/DocumentsTab";
import { DecksTab } from "../flashcards/DecksTab";
import { useDeleteSpace, useRenameSpace, useSpace } from "./hooks";
import { DeleteSpaceDialog, SpaceNameDialog } from "./SpaceDialogs";

const TABS = ["documents", "chat", "cards", "quizzes"] as const;
export type SpaceTab = (typeof TABS)[number];

export function isSpaceTab(value: unknown): value is SpaceTab {
  return TABS.includes(value as SpaceTab);
}

interface Props {
  id: string;
  initialTab?: SpaceTab | undefined;
  /** Conversation to open in the chat tab (from the history screen). */
  conversationId?: string | undefined;
}

export function SpaceDetailScreen({ id, initialTab, conversationId }: Props) {
  const { t } = useTranslation();
  const router = useRouter();
  const space = useSpace(id);
  const rename = useRenameSpace();
  const remove = useDeleteSpace();
  const [tab, setTab] = useState<SpaceTab>(initialTab ?? "documents");
  // The history screen navigates back here with new params; follow them.
  useEffect(() => {
    if (initialTab) setTab(initialTab);
  }, [initialTab, conversationId]);
  const [renaming, setRenaming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const backToList = () => router.replace("/spaces");

  if (space.isPending) {
    return (
      <View style={styles.center} testID="space-loading">
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (space.isError) {
    const missing =
      space.error instanceof ApiError && space.error.code === "NOT_FOUND";
    return (
      <View style={styles.center} testID="space-missing">
        <Text style={styles.muted}>
          {t(missing ? "spaces.notFound" : "spaces.loadError")}
        </Text>
        <Button
          label={t("spaces.backToList")}
          variant="secondary"
          onPress={backToList}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Pressable accessibilityRole="link" onPress={backToList}>
        <Text style={styles.link}>{t("spaces.backToList")}</Text>
      </Pressable>

      <View style={styles.header}>
        <Text
          style={styles.title}
          accessibilityRole="header"
          testID="space-title"
        >
          {space.data.name}
        </Text>
        <View style={styles.headerActions}>
          <Button
            label={t("spaces.rename")}
            variant="secondary"
            onPress={() => setRenaming(true)}
          />
          <Button
            label={t("common.delete")}
            variant="danger"
            onPress={() => setDeleting(true)}
          />
        </View>
      </View>

      <View style={styles.tabs} accessibilityRole="tablist">
        {TABS.map((key) => (
          <Pressable
            key={key}
            accessibilityRole="tab"
            accessibilityState={{ selected: tab === key }}
            onPress={() => setTab(key)}
            style={[styles.tab, tab === key && styles.tabActive]}
          >
            <Text style={[styles.tabText, tab === key && styles.tabTextActive]}>
              {t(`spaces.tabs.${key}`)}
            </Text>
          </Pressable>
        ))}
      </View>

      {tab === "documents" ? (
        <DocumentsTab spaceId={id} />
      ) : tab === "chat" ? (
        <ChatTab
          key={conversationId ?? "latest"}
          spaceId={id}
          initialConversationId={conversationId}
        />
      ) : tab === "cards" ? (
        <DecksTab spaceId={id} />
      ) : (
        // Quizzes arrive in F11.
        <View style={styles.placeholder} testID={`space-tab-${tab}`}>
          <Text style={styles.muted}>{t("spaces.comingSoon")}</Text>
        </View>
      )}

      <SpaceNameDialog
        visible={renaming}
        mode="rename"
        initialName={space.data.name}
        onSubmit={(name) => rename.mutateAsync({ id, name })}
        onClose={() => setRenaming(false)}
      />
      <DeleteSpaceDialog
        spaceName={deleting ? space.data.name : null}
        onConfirm={async () => {
          await remove.mutateAsync(id);
          backToList();
        }}
        onClose={() => setDeleting(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    flex: 1,
    gap: spacing.lg,
    maxWidth: 720,
    padding: spacing.xl,
    width: "100%",
  },
  center: {
    alignItems: "center",
    flex: 1,
    gap: spacing.md,
    justifyContent: "center",
    padding: spacing.xl,
  },
  header: { flexWrap: "wrap", gap: spacing.md },
  headerActions: { flexDirection: "row", gap: spacing.md },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  muted: {
    color: colors.textMuted,
    fontSize: fontSize.md,
    textAlign: "center",
  },
  tabs: {
    backgroundColor: colors.border,
    borderRadius: radius.md,
    flexDirection: "row",
    padding: 3,
  },
  tab: {
    alignItems: "center",
    borderRadius: radius.sm,
    flex: 1,
    paddingVertical: spacing.sm,
  },
  tabActive: { backgroundColor: colors.surface },
  tabText: {
    color: colors.textMuted,
    fontSize: fontSize.sm,
    fontWeight: "600",
  },
  tabTextActive: { color: colors.text },
  placeholder: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderStyle: "dashed",
    borderWidth: 1,
    padding: spacing.xxl,
  },
});
