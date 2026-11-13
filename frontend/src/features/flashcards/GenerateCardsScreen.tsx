import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { ChipGroup } from "../../components/ui/ChipGroup";
import { TextField } from "../../components/ui/TextField";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { useDocuments } from "../documents/hooks";
import {
  suggestFlashcards,
  type NewFlashcard,
  type SuggestionRequest,
} from "./api";
import { flashcardErrorText } from "./errors";
import { useAddCards, useCreateDeck, useDecks } from "./hooks";
import { SuggestionItem, type DraftCard } from "./SuggestionItem";

const COUNTS = ["5", "10", "20"];
const NEW_DECK = "__new__";

interface Props {
  spaceId: string;
  /** Save into this deck; without it the learner picks or names one. */
  deckId?: string | undefined;
  /** Make cards from this Q&A answer instead of a document. */
  messageId?: string | undefined;
}

/** Screen 13: the AI proposes cards; the learner edits, picks, then saves (U11). */
export function GenerateCardsScreen({ spaceId, deckId, messageId }: Props) {
  const { t } = useTranslation();
  const router = useRouter();
  const documents = useDocuments(spaceId);
  const decks = useDecks(spaceId);
  const createDeck = useCreateDeck(spaceId);
  const addCards = useAddCards();

  const ready = useMemo(
    () => (documents.data?.items ?? []).filter((d) => d.status === "READY"),
    [documents.data],
  );
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [pageFrom, setPageFrom] = useState("");
  const [pageTo, setPageTo] = useState("");
  const [count, setCount] = useState("10");
  const [targetDeck, setTargetDeck] = useState<string | null>(deckId ?? null);
  const [newDeckName, setNewDeckName] = useState("");
  const [drafts, setDrafts] = useState<DraftCard[]>([]);
  const [saveError, setSaveError] = useState<string | null>(null);

  const chosenDocument = documentId ?? ready[0]?.id ?? null;
  const suggest = useMutation({
    mutationFn: (request: SuggestionRequest) => suggestFlashcards(request),
    onSuccess: ({ items }) =>
      setDrafts(
        items.map((s, i) => ({ ...s, key: String(i), selected: true })),
      ),
  });

  function request(): SuggestionRequest | null {
    const source: SuggestionRequest["source"] | null = messageId
      ? { type: "message", message_id: messageId }
      : chosenDocument
        ? {
            type: "document",
            document_id: chosenDocument,
            page_start: toPage(pageFrom),
            page_end: toPage(pageTo),
          }
        : null;
    return source ? { space_id: spaceId, source, count: Number(count) } : null;
  }

  async function save() {
    const picked: NewFlashcard[] = drafts
      .filter((d) => d.selected && d.front.trim() && d.back.trim())
      .map((d) => ({
        front: d.front.trim(),
        back: d.back.trim(),
        origin: "ai",
        source: d.source?.document_id
          ? { document_id: d.source.document_id, page: d.source.page }
          : null,
      }));
    if (picked.length === 0) return;
    setSaveError(null);
    try {
      const deck =
        targetDeck && targetDeck !== NEW_DECK
          ? targetDeck
          : (
              await createDeck.mutateAsync(
                newDeckName.trim() || t("cards.defaultDeckName"),
              )
            ).id;
      await addCards.mutateAsync({ deckId: deck, cards: picked });
      router.replace({
        pathname: "/spaces/decks/[deckId]",
        params: { deckId: deck },
      });
    } catch (e) {
      setSaveError(flashcardErrorText(e, t));
    }
  }

  const selectedCount = drafts.filter((d) => d.selected).length;
  const deckOptions = [
    ...(decks.data?.items ?? []).map((d) => ({ value: d.id, label: d.name })),
    { value: NEW_DECK, label: t("cards.newDeck") },
  ];

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable
        accessibilityRole="link"
        onPress={() =>
          router.canGoBack() ? router.back() : router.replace("/spaces")
        }
      >
        <Text style={styles.link}>{t("common.back")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header">
        {t("cards.generateTitle")}
      </Text>

      <Section title={t("cards.sourceTitle")}>
        {messageId ? (
          <Text style={styles.muted}>{t("cards.fromAnswer")}</Text>
        ) : ready.length === 0 ? (
          <Text style={styles.muted} testID="generate-no-documents">
            {t("chat.noDocumentsHint")}
          </Text>
        ) : (
          <>
            <ChipGroup
              options={ready.map((d) => ({ value: d.id, label: d.filename }))}
              value={chosenDocument}
              onChange={setDocumentId}
              testID="generate-doc"
            />
            <View style={styles.pages}>
              <View style={styles.pageField}>
                <TextField
                  label={t("cards.pageFrom")}
                  value={pageFrom}
                  onChangeText={setPageFrom}
                  keyboardType="number-pad"
                  testID="generate-page-from"
                />
              </View>
              <View style={styles.pageField}>
                <TextField
                  label={t("cards.pageTo")}
                  value={pageTo}
                  onChangeText={setPageTo}
                  keyboardType="number-pad"
                />
              </View>
            </View>
          </>
        )}
        <Text style={styles.label}>{t("cards.countLabel")}</Text>
        <ChipGroup
          options={COUNTS.map((c) => ({ value: c, label: c }))}
          value={count}
          onChange={setCount}
        />
        <Button
          label={t(drafts.length ? "cards.suggestAgain" : "cards.suggest")}
          onPress={() => {
            const body = request();
            if (body) suggest.mutate(body);
          }}
          loading={suggest.isPending}
          disabled={!messageId && !chosenDocument}
          testID="generate-suggest"
        />
        {suggest.isError ? (
          <View style={styles.error} accessibilityRole="alert">
            <Text style={styles.errorText} testID="generate-error">
              {flashcardErrorText(suggest.error, t)}
            </Text>
            {deckId ? (
              <Text style={styles.muted}>{t("cards.manualHint")}</Text>
            ) : null}
          </View>
        ) : null}
      </Section>

      {drafts.length > 0 ? (
        <Section title={t("cards.reviewTitle", { count: selectedCount })}>
          {drafts.map((draft) => (
            <SuggestionItem
              key={draft.key}
              draft={draft}
              onChange={(next) =>
                setDrafts((all) =>
                  all.map((d) => (d.key === next.key ? next : d)),
                )
              }
            />
          ))}
          {deckId ? null : (
            <>
              <Text style={styles.label}>{t("cards.saveInto")}</Text>
              <ChipGroup
                options={deckOptions}
                value={targetDeck ?? NEW_DECK}
                onChange={setTargetDeck}
                testID="generate-deck"
              />
              {(targetDeck ?? NEW_DECK) === NEW_DECK ? (
                <TextField
                  label={t("cards.deckName")}
                  value={newDeckName}
                  onChangeText={setNewDeckName}
                  placeholder={t("cards.defaultDeckName")}
                />
              ) : null}
            </>
          )}
          {saveError ? <Text style={styles.errorText}>{saveError}</Text> : null}
          <Button
            label={t("cards.saveSelected", { count: selectedCount })}
            onPress={() => void save()}
            loading={addCards.isPending || createDeck.isPending}
            disabled={selectedCount === 0}
            testID="generate-save"
          />
        </Section>
      ) : null}
    </ScrollView>
  );
}

function toPage(text: string): number | null {
  const n = Number(text);
  return Number.isInteger(n) && n >= 1 ? n : null;
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    gap: spacing.lg,
    maxWidth: 720,
    padding: spacing.xl,
    width: "100%",
  },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  section: { gap: spacing.md },
  sectionTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "600",
  },
  label: { color: colors.text, fontSize: fontSize.sm, fontWeight: "600" },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  pages: { flexDirection: "row", gap: spacing.md },
  pageField: { flex: 1 },
  error: {
    backgroundColor: colors.dangerBg,
    borderRadius: radius.md,
    gap: spacing.xs,
    padding: spacing.md,
  },
  errorText: { color: colors.danger, fontSize: fontSize.sm },
});
