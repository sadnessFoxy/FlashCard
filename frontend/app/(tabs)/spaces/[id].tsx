import { useLocalSearchParams } from "expo-router";

import {
  SpaceDetailScreen,
  isSpaceTab,
} from "../../../src/features/spaces/SpaceDetailScreen";

export default function SpaceDetail() {
  const { id, tab, conversation } = useLocalSearchParams<{
    id: string;
    tab?: string;
    conversation?: string;
  }>();
  return (
    <SpaceDetailScreen
      id={id}
      initialTab={isSpaceTab(tab) ? tab : undefined}
      conversationId={conversation}
    />
  );
}
