import { api } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { components } from "../../api/generated/schema";
import { readSse } from "../../api/streaming";

type Schemas = components["schemas"];
export type Conversation = Schemas["Conversation"];
export type ConversationDetail = Schemas["ConversationDetail"];
export type ConversationList = Schemas["ConversationList"];
export type Message = Schemas["Message"];
export type Citation = Schemas["Citation"];
export type Usage = Schemas["Usage"];

/** Events of the answer stream, in order: start, citations, delta*, then done or error. */
export type ChatEvent =
  | { type: "start"; data: Schemas["ChatStartEvent"] }
  | { type: "citations"; data: Schemas["ChatCitationsEvent"] }
  | { type: "delta"; data: Schemas["ChatDeltaEvent"] }
  | { type: "done"; data: Schemas["ChatDoneEvent"] }
  | { type: "error"; data: Schemas["ChatErrorEvent"] };

const EVENT_TYPES = new Set(["start", "citations", "delta", "done", "error"]);

export function getUsage(signal?: AbortSignal): Promise<Usage> {
  return api.get<Usage>("/v1/usage/me", signal ? { signal } : {});
}

export function listConversations(
  spaceId: string,
  signal?: AbortSignal,
): Promise<ConversationList> {
  return api.get<ConversationList>(
    `/v1/conversations?space_id=${encodeURIComponent(spaceId)}`,
    signal ? { signal } : {},
  );
}

export function createConversation(spaceId: string): Promise<Conversation> {
  return api.post<Conversation>("/v1/conversations", { space_id: spaceId });
}

export function getConversation(
  id: string,
  signal?: AbortSignal,
): Promise<ConversationDetail> {
  return api.get<ConversationDetail>(
    `/v1/conversations/${encodeURIComponent(id)}`,
    signal ? { signal } : {},
  );
}

/**
 * Ask a question and stream the answer. Errors before the stream starts are thrown as
 * ApiError; errors during it arrive as an `error` event.
 */
export async function sendMessage(
  conversationId: string,
  content: string,
  documentIds: string[] | null,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await api.stream(
    `/v1/conversations/${encodeURIComponent(conversationId)}/messages`,
    { content, document_ids: documentIds },
    signal ? { signal } : {},
  );
  let finished = false;
  await readSse(response, ({ event, data }) => {
    if (!EVENT_TYPES.has(event)) return;
    if (event === "done" || event === "error") finished = true;
    onEvent({ type: event, data } as ChatEvent);
  });
  if (!finished) {
    // The connection dropped without a final event.
    throw new ApiError("NETWORK_ERROR", "Stream ended early");
  }
}

export function deleteConversation(id: string): Promise<void> {
  return api.delete<void>(`/v1/conversations/${encodeURIComponent(id)}`);
}
