import { useQueryClient } from "@tanstack/react-query";
import { useMemo, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { ApiError } from "../../api/errors";
import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { useDocuments } from "../documents/hooks";
import {
  createConversation,
  sendMessage,
  type Citation,
  type ConversationDetail,
  type Message,
} from "./api";
import { chatKeys, useConversation, useConversations, useUsage } from "./hooks";

const MAX_CHARS = 2000;

type Mode = Message["mode"];

interface LiveAnswer {
  question: string;
  text: string;
  citations: Citation[];
  mode: Mode;
}

interface Banner {
  code: string;
  resetAt?: Date | undefined;
}

export function ChatTab({ spaceId }: { spaceId: string }) {
  const { t, i18n } = useTranslation();
  const qc = useQueryClient();
  const documents = useDocuments(spaceId);
  const conversations = useConversations(spaceId);
  const usage = useUsage();

  // undefined: follow the latest conversation; null: a fresh one not created yet.
  const [chosen, setChosen] = useState<string | null | undefined>(undefined);
  const conversationId =
    chosen !== undefined ? chosen : (conversations.data?.items[0]?.id ?? null);
  const conversation = useConversation(conversationId);

  const [excluded, setExcluded] = useState<Set<string>>(new Set());
  const [draft, setDraft] = useState("");
  const [live, setLive] = useState<LiveAnswer | null>(null);
  const [banner, setBanner] = useState<Banner | null>(null);
  const [opened, setOpened] = useState<Citation | null>(null);
  const scroll = useRef<ScrollView>(null);

  const ready = useMemo(
    () => (documents.data?.items ?? []).filter((d) => d.status === "READY"),
    [documents.data],
  );
  const busy = live !== null;
  const messages = conversation.data?.messages ?? [];

  const toggle = (id: string) =>
    setExcluded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const selectedIds =
    excluded.size === 0
      ? null
      : ready.filter((d) => !excluded.has(d.id)).map((d) => d.id);

  async function ask() {
    const question = draft.trim();
    if (!question || busy || question.length > MAX_CHARS) return;
    setDraft("");
    setBanner(null);
    setLive({ question, text: "", citations: [], mode: "answer" });
    let id = conversationId;
    // Filled by stream callbacks; an object so TypeScript doesn't narrow it to null.
    const got: {
      user: Message | null;
      answer: Message | null;
      failure: Banner | null;
    } = { user: null, answer: null, failure: null };
    try {
      if (!id) {
        const created = await createConversation(spaceId);
        id = created.id;
        setChosen(created.id);
        qc.setQueryData<ConversationDetail>(chatKeys.detail(id), {
          ...created,
          messages: [],
        });
      }
      await sendMessage(id, question, selectedIds, (event) => {
        switch (event.type) {
          case "start":
            got.user = event.data.user_message;
            setLive((l) => l && { ...l, mode: event.data.mode });
            break;
          case "citations":
            setLive((l) => l && { ...l, citations: event.data.citations });
            break;
          case "delta":
            setLive((l) => l && { ...l, text: l.text + event.data.text });
            scroll.current?.scrollToEnd({ animated: false });
            break;
          case "done":
            got.answer = event.data.message;
            break;
          case "error":
            got.failure = {
              code: event.data.code,
              resetAt: event.data.quota_reset_at
                ? new Date(event.data.quota_reset_at)
                : undefined,
            };
            break;
        }
      });
    } catch (error) {
      got.failure =
        error instanceof ApiError
          ? { code: error.code, resetAt: error.details.quotaResetAt }
          : { code: "INTERNAL_ERROR" };
    }

    if (id) {
      const appended = [got.user, got.answer].filter(
        (m): m is Message => m !== null,
      );
      if (appended.length > 0) {
        qc.setQueryData<ConversationDetail>(chatKeys.detail(id), (prev) =>
          prev ? { ...prev, messages: [...prev.messages, ...appended] } : prev,
        );
      }
      void qc.invalidateQueries({ queryKey: chatKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: chatKeys.list(spaceId) });
    }
    void qc.invalidateQueries({ queryKey: chatKeys.usage });
    setLive(null);
    if (got.failure) {
      setBanner(got.failure);
      setDraft(question); // keep the question so it can be sent again
    }
  }

  const startNew = () => {
    if (busy) return;
    setChosen(null);
    setBanner(null);
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

  const quota = usage.data;

  return (
    <View style={styles.container} testID="chat-tab">
      <View style={styles.toolbar}>
        <Text style={styles.muted} testID="chat-quota">
          {quota
            ? t("chat.quota", {
                remaining: quota.remaining,
                limit: quota.daily_limit,
              })
            : " "}
        </Text>
        {messages.length > 0 ? (
          <Pressable
            accessibilityRole="button"
            onPress={startNew}
            disabled={busy}
            testID="chat-new"
          >
            <Text style={styles.link}>{t("chat.newConversation")}</Text>
          </Pressable>
        ) : null}
      </View>

      {ready.length > 1 ? (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chips}
        >
          {ready.map((d) => {
            const on = !excluded.has(d.id);
            return (
              <Pressable
                key={d.id}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: on }}
                onPress={() => toggle(d.id)}
                style={[styles.chip, on && styles.chipOn]}
                testID={`chat-doc-${d.id}`}
              >
                <Text
                  style={[styles.chipText, on && styles.chipTextOn]}
                  numberOfLines={1}
                >
                  {d.filename}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
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
              onOpen={setOpened}
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
              onOpen={setOpened}
            />
          </>
        ) : null}
      </ScrollView>

      {banner ? (
        <Text
          style={styles.banner}
          accessibilityRole="alert"
          testID="chat-error"
        >
          {errorText(banner, t, i18n.language)}
        </Text>
      ) : null}

      <View style={styles.inputRow}>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          placeholder={t("chat.placeholder")}
          placeholderTextColor={colors.textMuted}
          multiline
          maxLength={MAX_CHARS}
          editable={!busy}
          style={styles.input}
          accessibilityLabel={t("chat.placeholder")}
          testID="chat-input"
        />
        <Button
          label={t("chat.send")}
          onPress={() => void ask()}
          loading={busy}
          disabled={busy || draft.trim().length === 0}
          testID="chat-send"
        />
      </View>

      <Dialog
        visible={opened !== null}
        title={opened ? `[${opened.index}] ${opened.document_name}` : ""}
        onDismiss={() => setOpened(null)}
        testID="citation-dialog"
      >
        {opened ? (
          <>
            <Text style={styles.muted}>
              {pagesLabel(opened, t)}
              {opened.document_id === null
                ? ` · ${t("chat.deletedDocument")}`
                : ""}
            </Text>
            <ScrollView style={styles.snippetScroll}>
              <Text style={styles.snippet}>{opened.snippet}</Text>
            </ScrollView>
            <Button
              label={t("common.close")}
              variant="secondary"
              onPress={() => setOpened(null)}
            />
          </>
        ) : null}
      </Dialog>
    </View>
  );
}

type T = ReturnType<typeof useTranslation>["t"];

function pagesLabel(c: Citation, t: T): string {
  return c.page_start === c.page_end
    ? t("chat.page", { page: c.page_start })
    : t("chat.pages", { start: c.page_start, end: c.page_end });
}

function errorText(banner: Banner, t: T, language: string): string {
  switch (banner.code) {
    case "USER_QUOTA_EXCEEDED":
      return banner.resetAt
        ? t("chat.errors.quotaUntil", {
            time: banner.resetAt.toLocaleString(language, {
              hour: "2-digit",
              minute: "2-digit",
              day: "2-digit",
              month: "2-digit",
            }),
          })
        : t("chat.errors.quota");
    case "AI_TEMPORARILY_UNAVAILABLE":
    case "AI_RATE_LIMITED":
      return t("chat.errors.aiUnavailable");
    case "NETWORK_ERROR":
    case "TIMEOUT_ERROR":
      return t("chat.errors.network");
    case "NOT_FOUND":
      return t("chat.errors.notFound");
    case "VALIDATION_ERROR":
      return t("chat.errors.invalid");
    default:
      return t("chat.errors.generic");
  }
}

function UserBubble({ text }: { text: string }) {
  return (
    <View style={[styles.bubble, styles.userBubble]}>
      <Text style={styles.userText}>{text}</Text>
    </View>
  );
}

function AnswerBubble({
  mode,
  status,
  text,
  citations,
  onOpen,
}: {
  mode: Mode;
  status: Message["status"];
  text: string;
  citations: Citation[];
  onOpen: (c: Citation) => void;
}) {
  const { t } = useTranslation();
  const streaming = status === "pending";

  let body: ReactNode;
  if (mode === "not_found") {
    body = <Text style={styles.answerText}>{t("chat.notFound")}</Text>;
  } else if (mode === "retrieval_only") {
    body = (
      <>
        <Text style={styles.notice}>{t("chat.retrievalOnly")}</Text>
        {citations.map((c) => (
          <Pressable
            key={c.index}
            onPress={() => onOpen(c)}
            style={styles.passage}
            accessibilityRole="button"
          >
            <Text style={styles.passageTitle}>
              [{c.index}] {c.document_name} · {pagesLabel(c, t)}
            </Text>
            <Text style={styles.answerText} numberOfLines={4}>
              {c.snippet}
            </Text>
          </Pressable>
        ))}
      </>
    );
  } else if (streaming && text === "") {
    body = <Text style={styles.muted}>{t("chat.thinking")}</Text>;
  } else if (status === "error" && text === "") {
    body = <Text style={styles.notice}>{t("chat.failed")}</Text>;
  } else {
    body = (
      <>
        <Text style={styles.answerText}>{text}</Text>
        {status === "partial" ? (
          <Text style={styles.notice}>{t("chat.partial")}</Text>
        ) : null}
      </>
    );
  }

  return (
    <View style={[styles.bubble, styles.answerBubble]} testID="chat-answer">
      {body}
      {mode === "answer" && citations.length > 0 ? (
        <View style={styles.citations}>
          {citations.map((c) => (
            <Pressable
              key={c.index}
              onPress={() => onOpen(c)}
              style={styles.citation}
              accessibilityRole="button"
              testID={`citation-${c.index}`}
            >
              <Text style={styles.citationText} numberOfLines={1}>
                [{c.index}] {c.document_name} · {pagesLabel(c, t)}
              </Text>
            </Pressable>
          ))}
        </View>
      ) : null}
    </View>
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
  chips: { gap: spacing.sm },
  chip: {
    borderColor: colors.border,
    borderRadius: 999,
    borderWidth: 1,
    maxWidth: 220,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { color: colors.text, fontSize: fontSize.sm },
  chipTextOn: { color: colors.onPrimary },
  messages: { flex: 1 },
  messagesContent: { gap: spacing.md, paddingBottom: spacing.md },
  bubble: { borderRadius: radius.lg, gap: spacing.sm, padding: spacing.md },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: colors.primary,
    maxWidth: "85%",
  },
  userText: { color: colors.onPrimary, fontSize: fontSize.md },
  answerBubble: {
    alignSelf: "flex-start",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    maxWidth: "95%",
  },
  answerText: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  notice: {
    color: colors.textMuted,
    fontSize: fontSize.sm,
    fontStyle: "italic",
  },
  passage: {
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.sm,
  },
  passageTitle: {
    color: colors.text,
    fontSize: fontSize.sm,
    fontWeight: "600",
  },
  citations: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  citation: {
    backgroundColor: colors.background,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    maxWidth: 260,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
  },
  citationText: { color: colors.primary, fontSize: fontSize.sm },
  banner: {
    backgroundColor: colors.dangerBg,
    borderRadius: radius.md,
    color: colors.danger,
    fontSize: fontSize.sm,
    padding: spacing.md,
  },
  inputRow: { alignItems: "flex-end", flexDirection: "row", gap: spacing.sm },
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
  snippetScroll: { maxHeight: 280 },
  snippet: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
});
