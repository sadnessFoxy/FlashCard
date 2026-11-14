import { api } from "../../api/client";
import type { components } from "../../api/generated/schema";

export type Section = components["schemas"]["Section"];
export type SectionList = components["schemas"]["SectionList"];
export type Summary = components["schemas"]["Summary"];

const sectionsPath = (documentId: string) =>
  `/v1/documents/${encodeURIComponent(documentId)}/sections`;

export function listSections(documentId: string, signal?: AbortSignal) {
  return api.get<SectionList>(
    sectionsPath(documentId),
    signal ? { signal } : {},
  );
}

/** Returns the saved summary when it already exists (no quota used). */
export function summarizeSection(documentId: string, sectionId: string) {
  return api.post<Summary>(
    `${sectionsPath(documentId)}/${encodeURIComponent(sectionId)}/summary`,
    undefined,
    { timeoutMs: 90_000 },
  );
}
