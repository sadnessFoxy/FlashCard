import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError } from "../../api/errors";
import {
  createConversation,
  sendMessage,
  type Citation,
  type ConversationDetail,
  type Message,
} from "./api";
import { chatKeys } from "./hooks";

/** The answer being streamed right now. */
export interface LiveAnswer {
  question: string;
  text: string;
  citations: Citation[];
  mode: Message["mode"];
}

export interface ChatFailure {
  code: string;
  resetAt?: Date | undefined;
}

interface Options {
  spaceId: string;
  conversationId: string | null;
  /** Called once a fresh conversation has been created for the first question. */
  onConversationCreated: (id: string) => void;
  /** Called after each streamed piece of text (e.g. to scroll). */
  onText?: () => void;
}

/**
 * Sends a question and plays the streamed answer into `live`. Saved messages are put into
 * the conversation cache, so the list shows them as soon as the stream ends.
 */
export function useAskQuestion({
  spaceId,
  conversationId,
  onConversationCreated,
  onText,
}: Options) {
  const qc = useQueryClient();
  const [live, setLive] = useState<LiveAnswer | null>(null);
  const [failure, setFailure] = useState<ChatFailure | null>(null);

  async function ensureConversation(): Promise<string> {
    if (conversationId) return conversationId;
    const created = await createConversation(spaceId);
    qc.setQueryData<ConversationDetail>(chatKeys.detail(created.id), {
      ...created,
      messages: [],
    });
    onConversationCreated(created.id);
    return created.id;
  }

  function saveToCache(id: string, saved: Message[]) {
    if (saved.length > 0) {
      qc.setQueryData<ConversationDetail>(chatKeys.detail(id), (prev) =>
        prev ? { ...prev, messages: [...prev.messages, ...saved] } : prev,
      );
    }
    void qc.invalidateQueries({ queryKey: chatKeys.detail(id) });
    void qc.invalidateQueries({ queryKey: chatKeys.list(spaceId) });
  }

  /** Resolves to true when the answer arrived, false when it failed. */
  async function ask(
    question: string,
    documentIds: string[] | null,
  ): Promise<boolean> {
    setFailure(null);
    setLive({ question, text: "", citations: [], mode: "answer" });
    const saved: Message[] = [];
    let failed: ChatFailure | null = null;
    let id: string | null = null;

    try {
      id = await ensureConversation();
      await sendMessage(id, question, documentIds, (event) => {
        switch (event.type) {
          case "start":
            saved.push(event.data.user_message);
            setLive((l) => l && { ...l, mode: event.data.mode });
            break;
          case "citations":
            setLive((l) => l && { ...l, citations: event.data.citations });
            break;
          case "delta":
            setLive((l) => l && { ...l, text: l.text + event.data.text });
            onText?.();
            break;
          case "done":
            saved.push(event.data.message);
            break;
          case "error":
            failed = {
              code: event.data.code,
              resetAt: event.data.quota_reset_at
                ? new Date(event.data.quota_reset_at)
                : undefined,
            };
            break;
        }
      });
    } catch (error) {
      failed =
        error instanceof ApiError
          ? { code: error.code, resetAt: error.details.quotaResetAt }
          : { code: "INTERNAL_ERROR" };
    }

    if (id) saveToCache(id, saved);
    void qc.invalidateQueries({ queryKey: chatKeys.usage });
    setLive(null);
    setFailure(failed);
    return failed === null;
  }

  return {
    live,
    failure,
    busy: live !== null,
    ask,
    clearFailure: () => setFailure(null),
  };
}
