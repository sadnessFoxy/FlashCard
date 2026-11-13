import { useLocalSearchParams } from "expo-router";

import { GenerateCardsScreen } from "../../../../src/features/flashcards/GenerateCardsScreen";

export default function GenerateCards() {
  const { spaceId, deckId, messageId } = useLocalSearchParams<{
    spaceId: string;
    deckId?: string;
    messageId?: string;
  }>();
  return (
    <GenerateCardsScreen
      spaceId={spaceId}
      deckId={deckId}
      messageId={messageId}
    />
  );
}
