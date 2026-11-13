import { useLocalSearchParams } from "expo-router";

import { ReviewScreen } from "../../../src/features/reviews/ReviewScreen";

export default function Review() {
  const { spaceId, deckId } = useLocalSearchParams<{
    spaceId: string;
    deckId?: string;
  }>();
  return <ReviewScreen spaceId={spaceId} deckId={deckId} />;
}
