import { useLocalSearchParams } from "expo-router";

import { DocumentDetailScreen } from "../../../../src/features/documents/DocumentDetailScreen";

export default function DocumentDetail() {
  const { documentId } = useLocalSearchParams<{ documentId: string }>();
  return <DocumentDetailScreen id={documentId} />;
}
