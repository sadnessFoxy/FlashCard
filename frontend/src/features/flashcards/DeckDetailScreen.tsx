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

import { ApiError } from "../../api/errors";
import { ConfirmDialog } from "../../components/feedback/ConfirmDialog";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, spacing } from "../../theme/tokens";
import type { Flashcard } from "./api";
import { CardEditorDialog } from "./CardEditorDialog";
import { CardRow } from "./CardRow";
import { DeckNameDialog } from "./DeckNameDialog";
import { flashcardErrorText } from "./errors";
import {
  useAddCards,
  useDeck,
  useDeleteCard,
  useDeleteDeck,
  useRenameDeck,
  useUpdateCard,
} from "./hooks";

type Editing = { mode: "add" } | { mode: "edit"; card: Flashcard } | null;

/** Screen 14: a deck's cards; add, edit, delete, open sources, make cards with AI. */
export function DeckDetailScreen({ deckId }: { deckId: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const deck = useDeck(deckId);
  const rename = useRenameDeck(deckId);
  const removeDeck = useDeleteDeck();
  const addCards = useAddCards();
  const updateCard = useUpdateCard();
  const removeCard = useDeleteCard();

  const [editing, setEditing] = useState<Editing>(null);
  const [renaming, setRenaming] = useState(false);
  const [deletingDeck, setDeletingDeck] = useState(false);
  const [deletingCard, setDeletingCard] = useState<Flashcard | null>(null);

  const goBack = () =>
    router.canGoBack() ? router.back() : router.replace("/spaces");

  if (deck.isPending) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  if (deck.isError) {
    const missing =
      deck.error instanceof ApiError && deck.error.code === "NOT_FOUND";
    return (
      <View style={styles.center} testID="deck-missing">
        <Text style={styles.muted}>
          {t(missing ? "cards.errors.notFound" : "cards.loadError")}
        </Text>
        <Button label={t("common.back")} variant="secondary" onPress={goBack} />
      </View>
    );
  }

  const data = deck.data;
  const openSource = (card: Flashcard) => {
    if (!card.source?.document_id || !card.source.page) return;
    router.push({
      pathname: "/spaces/citation",
      params: {
        documentId: card.source.document_id,
        page: String(card.source.page),
        highlight: card.back,
      },
    });
  };

  return (
    <View style={styles.container}>
      <Pressable accessibilityRole="link" onPress={goBack}>
        <Text style={styles.link}>{t("common.back")}</Text>
      </Pressable>
      <Text style={styles.title} accessibilityRole="header" testID="deck-title">
        {data.name}
      </Text>
      <Text style={styles.muted}>
        {t("cards.cardCount", { count: data.card_count })}
        {" · "}
        {data.due_count > 0
          ? t("cards.dueCount", { count: data.due_count })
          : t("cards.nothingDue")}
      </Text>

      <View style={styles.actions}>
        <Button
          label={t("cards.generate")}
          onPress={() =>
            router.push({
              pathname: "/spaces/decks/generate",
              params: { spaceId: data.space_id, deckId: data.id },
            })
          }
          testID="deck-generate"
        />
        <Button
          label={t("cards.addCard")}
          variant="secondary"
          onPress={() => setEditing({ mode: "add" })}
          testID="deck-add-card"
        />
        <Button
          label={t("spaces.rename")}
          variant="secondary"
          onPress={() => setRenaming(true)}
        />
        <Button
          label={t("common.delete")}
          variant="danger"
          onPress={() => setDeletingDeck(true)}
          testID="deck-delete"
        />
      </View>

      <FlatList
        data={data.cards}
        keyExtractor={(c) => c.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.muted} testID="deck-empty">
            {t("cards.deckEmpty")}
          </Text>
        }
        renderItem={({ item }) => (
          <CardRow
            card={item}
            onEdit={() => setEditing({ mode: "edit", card: item })}
            onDelete={() => setDeletingCard(item)}
            onOpenSource={() => openSource(item)}
          />
        )}
      />

      <CardEditorDialog
        visible={editing !== null}
        title={t(editing?.mode === "edit" ? "cards.editCard" : "cards.addCard")}
        initial={editing?.mode === "edit" ? editing.card : undefined}
        errorText={(e) => flashcardErrorText(e, t)}
        onSave={(front, back) =>
          editing?.mode === "edit"
            ? updateCard.mutateAsync({ id: editing.card.id, front, back })
            : addCards.mutateAsync({
                deckId,
                cards: [{ front, back, origin: "manual" }],
              })
        }
        onClose={() => setEditing(null)}
      />
      <DeckNameDialog
        visible={renaming}
        title={t("cards.renameDeck")}
        initialName={data.name}
        onSubmit={(name) => rename.mutateAsync(name)}
        onClose={() => setRenaming(false)}
      />
      <ConfirmDialog
        visible={deletingDeck}
        title={t("cards.deleteDeckTitle", { name: data.name })}
        message={t("cards.deleteDeckWarning")}
        confirmLabel={t("common.delete")}
        cancelLabel={t("common.cancel")}
        busy={removeDeck.isPending}
        onConfirm={() =>
          removeDeck.mutate(deckId, {
            onSuccess: () => {
              setDeletingDeck(false);
              goBack();
            },
          })
        }
        onCancel={() => setDeletingDeck(false)}
        testID="deck-delete-dialog"
      />
      <ConfirmDialog
        visible={deletingCard !== null}
        title={t("cards.deleteCardTitle")}
        message={deletingCard?.front ?? ""}
        confirmLabel={t("common.delete")}
        cancelLabel={t("common.cancel")}
        busy={removeCard.isPending}
        onConfirm={() =>
          deletingCard &&
          removeCard.mutate(deletingCard.id, {
            onSettled: () => setDeletingCard(null),
          })
        }
        onCancel={() => setDeletingCard(null)}
        testID="card-delete-dialog"
      />
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
  center: {
    alignItems: "center",
    flex: 1,
    gap: spacing.md,
    justifyContent: "center",
    padding: spacing.xl,
  },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  actions: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  list: { gap: spacing.sm, paddingBottom: spacing.xl },
});
