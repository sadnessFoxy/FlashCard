import { useLocalSearchParams } from "expo-router";

import { SpaceDetailScreen } from "../../../src/features/spaces/SpaceDetailScreen";

export default function SpaceDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <SpaceDetailScreen id={id} />;
}
