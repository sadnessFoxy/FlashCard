import { useLocalSearchParams } from "expo-router";

import { DeckDetailScreen } from "../../../../src/features/flashcards/DeckDetailScreen";

export default function DeckDetail() {
  const { deckId } = useLocalSearchParams<{ deckId: string }>();
  return <DeckDetailScreen deckId={deckId} />;
}
