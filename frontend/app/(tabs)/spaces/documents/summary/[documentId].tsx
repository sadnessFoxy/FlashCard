import { useLocalSearchParams } from "expo-router";

import { SummaryScreen } from "../../../../../src/features/summaries/SummaryScreen";

export default function DocumentSummary() {
  const { documentId } = useLocalSearchParams<{ documentId: string }>();
  return <SummaryScreen documentId={documentId} />;
}
