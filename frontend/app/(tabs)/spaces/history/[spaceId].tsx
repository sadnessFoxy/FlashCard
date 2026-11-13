import { useLocalSearchParams } from "expo-router";

import { ConversationHistoryScreen } from "../../../../src/features/chat/ConversationHistoryScreen";

export default function ConversationHistory() {
  const { spaceId } = useLocalSearchParams<{ spaceId: string }>();
  return <ConversationHistoryScreen spaceId={spaceId} />;
}
