import { useLocalSearchParams } from "expo-router";

import { CitationPageScreen } from "../../../src/features/documents/CitationPageScreen";

export default function CitationPage() {
  const { documentId, page, highlight } = useLocalSearchParams<{
    documentId: string;
    page: string;
    highlight?: string;
  }>();
  return (
    <CitationPageScreen
      documentId={documentId}
      page={Math.max(1, Number(page) || 1)}
      highlight={highlight ?? ""}
    />
  );
}
