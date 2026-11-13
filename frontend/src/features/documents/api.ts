import { api } from "../../api/client";
import type { components } from "../../api/generated/schema";

export type DocumentItem = components["schemas"]["Document"];
export type DocumentStatus = components["schemas"]["DocumentStatus"];
export type DocumentList = components["schemas"]["DocumentList"];
type ConsentList = components["schemas"]["ConsentList"];
type Consent = components["schemas"]["Consent"];

export const AI_CONSENT_KIND = "ai_processing";

/** A file picked on web (File) or native (uri + name), ready for multipart upload. */
export interface PickedFile {
  name: string;
  size?: number | null;
  mimeType?: string | null;
  uri: string;
  file?: Blob | null; // present on web
}

export function listDocuments(
  spaceId: string,
  signal?: AbortSignal,
): Promise<DocumentList> {
  const query = `space_id=${encodeURIComponent(spaceId)}`;
  return api.get<DocumentList>(
    `/v1/documents?${query}`,
    signal ? { signal } : {},
  );
}

export function uploadDocument(
  spaceId: string,
  picked: PickedFile,
  idempotencyKey: string,
): Promise<DocumentItem> {
  const form = new FormData();
  form.append("space_id", spaceId);
  if (picked.file) {
    form.append("file", picked.file, picked.name);
  } else {
    // React Native's FormData accepts a { uri, name, type } descriptor for files.
    form.append("file", {
      uri: picked.uri,
      name: picked.name,
      type: picked.mimeType ?? "application/pdf",
    } as unknown as Blob);
  }
  return api.post<DocumentItem>("/v1/documents", form, {
    headers: { "Idempotency-Key": idempotencyKey },
    timeoutMs: 120_000,
  });
}

export async function hasCurrentAiConsent(): Promise<{
  ok: boolean;
  version: string;
}> {
  const body = await api.get<ConsentList>("/v1/me/consents");
  const version = body.current_versions[AI_CONSENT_KIND] ?? "";
  return {
    ok: body.items.some(
      (c) => c.kind === AI_CONSENT_KIND && c.version === version,
    ),
    version,
  };
}

export function giveAiConsent(version: string): Promise<Consent> {
  return api.post<Consent>("/v1/me/consents", {
    kind: AI_CONSENT_KIND,
    version,
  });
}

export function getDocument(
  id: string,
  signal?: AbortSignal,
): Promise<DocumentItem> {
  return api.get<DocumentItem>(
    `/v1/documents/${encodeURIComponent(id)}`,
    signal ? { signal } : {},
  );
}

export function retryDocument(id: string): Promise<DocumentItem> {
  return api.post<DocumentItem>(
    `/v1/documents/${encodeURIComponent(id)}/retry`,
  );
}

export function deleteDocument(id: string): Promise<void> {
  return api.delete<void>(`/v1/documents/${encodeURIComponent(id)}`);
}

export function moveDocument(
  id: string,
  spaceId: string,
): Promise<DocumentItem> {
  return api.post<DocumentItem>(
    `/v1/documents/${encodeURIComponent(id)}/move`,
    {
      space_id: spaceId,
    },
  );
}

export type DocumentPage = components["schemas"]["DocumentPage"];

export function getDocumentPage(
  id: string,
  page: number,
  signal?: AbortSignal,
): Promise<DocumentPage> {
  return api.get<DocumentPage>(
    `/v1/documents/${encodeURIComponent(id)}/pages/${page}`,
    signal ? { signal } : {},
  );
}
