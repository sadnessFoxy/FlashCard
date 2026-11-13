import { useRouter } from "expo-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { Deck } from "./api";
import { DeckNameDialog } from "./DeckNameDialog";
import { useCreateDeck, useDecks } from "./hooks";

/** Screen 12: the decks of a space with card and due counts. */
export function DecksTab({ spaceId }: { spaceId: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const decks = useDecks(spaceId);
  const create = useCreateDeck(spaceId);
  const [creating, setCreating] = useState(false);

  const openDeck = (deck: Deck) =>
    router.push({
      pathname: "/spaces/decks/[deckId]",
      params: { deckId: deck.id },
    });

  if (decks.isPending) {
    return <ActivityIndicator color={colors.primary} testID="decks-loading" />;
  }
  if (decks.isError) {
    return <Text style={styles.muted}>{t("cards.loadError")}</Text>;
  }

  const totalDue = decks.data.items.reduce((sum, d) => sum + d.due_count, 0);

  return (
    <View style={styles.container}>
      {totalDue > 0 ? (
        <Button
          label={t("review.startAll", { count: totalDue })}
          onPress={() =>
            router.push({ pathname: "/spaces/review", params: { spaceId } })
          }
          testID="decks-review"
        />
      ) : null}
      <Button
        label={t("cards.newDeck")}
        variant={totalDue > 0 ? "secondary" : "primary"}
        onPress={() => setCreating(true)}
        testID="decks-create"
      />
      {decks.data.items.length === 0 ? (
        <View style={styles.empty} testID="decks-empty">
          <Text style={styles.emptyTitle}>{t("cards.emptyTitle")}</Text>
          <Text style={styles.muted}>{t("cards.emptyHint")}</Text>
        </View>
      ) : (
        decks.data.items.map((deck) => (
          <Pressable
            key={deck.id}
            style={styles.row}
            accessibilityRole="button"
            onPress={() => openDeck(deck)}
            testID={`deck-${deck.id}`}
          >
            <Text style={styles.name}>{deck.name}</Text>
            <Text style={styles.muted}>
              {t("cards.cardCount", { count: deck.card_count })}
              {" · "}
              {deck.due_count > 0
                ? t("cards.dueCount", { count: deck.due_count })
                : t("cards.nothingDue")}
            </Text>
          </Pressable>
        ))
      )}

      <DeckNameDialog
        visible={creating}
        title={t("cards.newDeck")}
        onSubmit={async (name) => {
          const deck = await create.mutateAsync(name);
          openDeck(deck);
        }}
        onClose={() => setCreating(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.md },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
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
  row: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  name: { color: colors.text, fontSize: fontSize.md, fontWeight: "600" },
});
