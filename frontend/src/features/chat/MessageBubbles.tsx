import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { Citation, Message } from "./api";
import { pagesLabel } from "./labels";

export function UserBubble({ text }: { text: string }) {
  return (
    <View style={[styles.bubble, styles.user]}>
      <Text style={styles.userText}>{text}</Text>
    </View>
  );
}

interface AnswerProps {
  mode: Message["mode"];
  status: Message["status"];
  text: string;
  citations: Citation[];
  onOpenCitation: (c: Citation) => void;
}

export function AnswerBubble(props: AnswerProps) {
  const showChips = props.mode === "answer" && props.citations.length > 0;
  return (
    <View style={[styles.bubble, styles.answer]} testID="chat-answer">
      <AnswerBody {...props} />
      {showChips ? (
        <CitationChips
          citations={props.citations}
          onOpen={props.onOpenCitation}
        />
      ) : null}
    </View>
  );
}

function AnswerBody({
  mode,
  status,
  text,
  citations,
  onOpenCitation,
}: AnswerProps): ReactNode {
  const { t } = useTranslation();
  if (mode === "not_found") {
    return <Text style={styles.text}>{t("chat.notFound")}</Text>;
  }
  if (mode === "retrieval_only") {
    return (
      <>
        <Text style={styles.notice}>{t("chat.retrievalOnly")}</Text>
        {citations.map((c) => (
          <Pressable
            key={c.index}
            onPress={() => onOpenCitation(c)}
            style={styles.passage}
            accessibilityRole="button"
          >
            <Text style={styles.passageTitle}>
              [{c.index}] {c.document_name} · {pagesLabel(c, t)}
            </Text>
            <Text style={styles.text} numberOfLines={4}>
              {c.snippet}
            </Text>
          </Pressable>
        ))}
      </>
    );
  }
  if (status === "pending" && text === "") {
    return <Text style={styles.muted}>{t("chat.thinking")}</Text>;
  }
  if (status === "error" && text === "") {
    return <Text style={styles.notice}>{t("chat.failed")}</Text>;
  }
  return (
    <>
      <Text style={styles.text}>{text}</Text>
      {status === "partial" ? (
        <Text style={styles.notice}>{t("chat.partial")}</Text>
      ) : null}
    </>
  );
}

function CitationChips({
  citations,
  onOpen,
}: {
  citations: Citation[];
  onOpen: (c: Citation) => void;
}) {
  const { t } = useTranslation();
  return (
    <View style={styles.chips}>
      {citations.map((c) => (
        <Pressable
          key={c.index}
          onPress={() => onOpen(c)}
          style={styles.chip}
          accessibilityRole="button"
          testID={`citation-${c.index}`}
        >
          <Text style={styles.chipText} numberOfLines={1}>
            [{c.index}] {c.document_name} · {pagesLabel(c, t)}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  bubble: { borderRadius: radius.lg, gap: spacing.sm, padding: spacing.md },
  user: {
    alignSelf: "flex-end",
    backgroundColor: colors.primary,
    maxWidth: "85%",
  },
  userText: { color: colors.onPrimary, fontSize: fontSize.md },
  answer: {
    alignSelf: "flex-start",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    maxWidth: "95%",
  },
  text: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
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
  chips: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  chip: {
    backgroundColor: colors.background,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    maxWidth: 260,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
  },
  chipText: { color: colors.primary, fontSize: fontSize.sm },
});
