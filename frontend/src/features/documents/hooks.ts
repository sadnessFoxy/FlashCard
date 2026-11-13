import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  giveAiConsent,
  hasCurrentAiConsent,
  listDocuments,
  uploadDocument,
  type DocumentList,
  type DocumentStatus,
  type PickedFile,
} from "./api";

const POLL_MS = 3_000;
const IN_PROGRESS: ReadonlySet<DocumentStatus> = new Set([
  "UPLOADED",
  "QUEUED",
  "PROCESSING",
]);

export const documentKeys = {
  inSpace: (spaceId: string) => ["documents", spaceId] as const,
  consent: ["consents", "ai"] as const,
};

export function isInProgress(status: DocumentStatus): boolean {
  return IN_PROGRESS.has(status);
}

export function useDocuments(spaceId: string) {
  return useQuery({
    queryKey: documentKeys.inSpace(spaceId),
    queryFn: ({ signal }) => listDocuments(spaceId, signal),
    // Poll only while something is still being processed.
    refetchInterval: (query) =>
      query.state.data?.items.some((d) => isInProgress(d.status))
        ? POLL_MS
        : false,
  });
}

export function useAiConsent() {
  return useQuery({
    queryKey: documentKeys.consent,
    queryFn: hasCurrentAiConsent,
  });
}

export function useGiveAiConsent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (version: string) => giveAiConsent(version),
    onSuccess: (_c, version) =>
      qc.setQueryData(documentKeys.consent, { ok: true, version }),
  });
}

export function useUploadDocument(spaceId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ file, key }: { file: PickedFile; key: string }) =>
      uploadDocument(spaceId, file, key),
    onSuccess: (doc) => {
      qc.setQueryData<DocumentList>(documentKeys.inSpace(spaceId), (prev) =>
        prev
          ? {
              ...prev,
              items: [doc, ...prev.items.filter((d) => d.id !== doc.id)],
              total_documents: prev.items.some((d) => d.id === doc.id)
                ? prev.total_documents
                : prev.total_documents + 1,
            }
          : prev,
      );
      void qc.invalidateQueries({ queryKey: documentKeys.inSpace(spaceId) });
    },
  });
}
