import { useRouter } from "expo-router";
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { useDocuments } from "../documents/hooks";
import type { Citation } from "./api";
import { CitationDialog } from "./CitationDialog";
import { DocumentChips } from "./DocumentChips";
import { useConversation, useConversations, useUsage } from "./hooks";
import { chatErrorText } from "./labels";
import { AnswerBubble, UserBubble } from "./MessageBubbles";
import { MAX_QUESTION_CHARS, QuestionInput } from "./QuestionInput";
import { useAskQuestion } from "./useAskQuestion";

interface Props {
  spaceId: string;
  /** Open this conversation instead of the latest one (from the history screen). */
  initialConversationId?: string | undefined;
}

export function ChatTab({ spaceId, initialConversationId }: Props) {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const documents = useDocuments(spaceId);
  const conversations = useConversations(spaceId);
  const usage = useUsage();
  const scroll = useRef<ScrollView>(null);

  // undefined: follow the latest conversation; null: a fresh one not created yet.
  const [chosen, setChosen] = useState<string | null | undefined>(
    initialConversationId,
  );
  const conversationId =
    chosen !== undefined ? chosen : (conversations.data?.items[0]?.id ?? null);
  const conversation = useConversation(conversationId);
  const messages = conversation.data?.messages ?? [];

  const [excluded, setExcluded] = useState<Set<string>>(new Set());
  const [draft, setDraft] = useState("");
  const [opened, setOpened] = useState<Citation | null>(null);
  const { live, failure, busy, ask, clearFailure } = useAskQuestion({
    spaceId,
    conversationId,
    onConversationCreated: setChosen,
    onText: () => scroll.current?.scrollToEnd({ animated: false }),
  });

  const ready = useMemo(
    () => (documents.data?.items ?? []).filter((d) => d.status === "READY"),
    [documents.data],
  );

  const toggleDocument = (id: string) =>
    setExcluded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  async function send() {
    const question = draft.trim();
    if (!question || busy || question.length > MAX_QUESTION_CHARS) return;
    const selected =
      excluded.size === 0
        ? null
        : ready.filter((d) => !excluded.has(d.id)).map((d) => d.id);
    setDraft("");
    const ok = await ask(question, selected);
    if (!ok) setDraft(question); // keep the question so it can be sent again
  }

  const startNew = () => {
    if (busy) return;
    setChosen(null);
    clearFailure();
  };

  if (documents.isPending || conversations.isPending) {
    return (
      <View style={styles.center} testID="chat-loading">
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (ready.length === 0 && messages.length === 0) {
    return (
      <View style={styles.empty} testID="chat-no-documents">
        <Text style={styles.emptyTitle}>{t("chat.noDocumentsTitle")}</Text>
        <Text style={styles.muted}>{t("chat.noDocumentsHint")}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container} testID="chat-tab">
      <View style={styles.toolbar}>
        <Text style={styles.muted} testID="chat-quota">
          {usage.data
            ? t("chat.quota", {
                remaining: usage.data.remaining,
                limit: usage.data.daily_limit,
              })
            : " "}
        </Text>
        <View style={styles.toolbarLinks}>
          <Link
            label={t("chat.history")}
            onPress={() =>
              router.push({
                pathname: "/spaces/history/[spaceId]",
                params: { spaceId },
              })
            }
            testID="chat-history"
          />
          {messages.length > 0 ? (
            <Link
              label={t("chat.newConversation")}
              onPress={startNew}
              disabled={busy}
              testID="chat-new"
            />
          ) : null}
        </View>
      </View>

      {ready.length > 1 ? (
        <DocumentChips
          documents={ready}
          excluded={excluded}
          onToggle={toggleDocument}
        />
      ) : null}

      <ScrollView
        ref={scroll}
        style={styles.messages}
        contentContainerStyle={styles.messagesContent}
        onContentSizeChange={() =>
          scroll.current?.scrollToEnd({ animated: false })
        }
      >
        {messages.length === 0 && !live ? (
          <Text style={styles.muted}>{t("chat.emptyHint")}</Text>
        ) : null}
        {messages.map((m) =>
          m.role === "user" ? (
            <UserBubble key={m.id} text={m.content} />
          ) : (
            <AnswerBubble
              key={m.id}
              mode={m.mode}
              status={m.status}
              text={m.content}
              citations={m.citations}
              onOpenCitation={setOpened}
            />
          ),
        )}
        {live ? (
          <>
            <UserBubble text={live.question} />
            <AnswerBubble
              mode={live.mode}
              status="pending"
              text={live.text}
              citations={live.citations}
              onOpenCitation={setOpened}
            />
          </>
        ) : null}
      </ScrollView>

      {failure ? (
        <Text
          style={styles.banner}
          accessibilityRole="alert"
          testID="chat-error"
        >
          {chatErrorText(failure, t, i18n.language)}
        </Text>
      ) : null}

      <QuestionInput
        value={draft}
        onChange={setDraft}
        onSend={() => void send()}
        busy={busy}
      />

      <CitationDialog citation={opened} onClose={() => setOpened(null)} />
    </View>
  );
}

function Link({
  label,
  onPress,
  disabled,
  testID,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  testID: string;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={disabled}
      testID={testID}
    >
      <Text style={styles.link}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, gap: spacing.md, minHeight: 420 },
  center: { alignItems: "center", padding: spacing.xl },
  empty: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderStyle: "dashed",
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.xxl,
  },
  emptyTitle: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  toolbar: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  toolbarLinks: { flexDirection: "row", gap: spacing.lg },
  messages: { flex: 1 },
  messagesContent: { gap: spacing.md, paddingBottom: spacing.md },
  banner: {
    backgroundColor: colors.dangerBg,
    borderRadius: radius.md,
    color: colors.danger,
    fontSize: fontSize.sm,
    padding: spacing.md,
  },
});
