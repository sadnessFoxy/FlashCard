import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { listSections, summarizeSection, type SectionList } from "./api";

const sectionsKey = (documentId: string) => ["sections", documentId] as const;

export function useSections(documentId: string) {
  return useQuery({
    queryKey: sectionsKey(documentId),
    queryFn: ({ signal }) => listSections(documentId, signal),
    retry: false,
  });
}

export function useSummarize(documentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sectionId: string) => summarizeSection(documentId, sectionId),
    onSuccess: (summary, sectionId) => {
      qc.setQueryData<SectionList>(sectionsKey(documentId), (prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((s) =>
                s.id === sectionId ? { ...s, summary } : s,
              ),
            }
          : prev,
      );
      void qc.invalidateQueries({ queryKey: ["usage"] });
    },
  });
}
