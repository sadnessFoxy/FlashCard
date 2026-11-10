/**
 * Server-Sent Events (SSE) reader for streaming Q&A.
 * Each event is a JSON chunk as defined in contract/openapi.yaml.
 */

import { ApiError, type ApiErrorCode } from "./errors";

export interface StreamChunk {
  type: "text" | "citation" | "error" | "done";
  content?: string;
  citations?: Array<{
    document_id: string;
    page: number;
    excerpt: string;
  }>;
  error_code?: ApiErrorCode;
  error_message?: string;
}

export type StreamChunkCallback = (chunk: StreamChunk) => void;
export type StreamErrorCallback = (error: ApiError) => void;
export type StreamDoneCallback = () => void;

/**
 * Read an SSE response and invoke the callbacks per chunk.
 */
export async function readStream(
  response: Response,
  onChunk: StreamChunkCallback,
  onError: StreamErrorCallback,
  onDone: StreamDoneCallback,
): Promise<void> {
  if (!response.body) {
    onError(new ApiError("INTERNAL_SERVER_ERROR", "Response body is empty"));
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        onDone();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();
          if (data === "[DONE]") {
            onDone();
            return;
          }

          try {
            const chunk = JSON.parse(data) as StreamChunk;

            if (chunk.type === "error" && chunk.error_code) {
              onError(
                new ApiError(
                  chunk.error_code,
                  chunk.error_message ?? "Stream error",
                ),
              );
              return;
            }

            onChunk(chunk);
          } catch {
            // Skip lines that are not valid JSON
          }
        }
      }
    }
  } catch (error) {
    if (error instanceof Error) {
      onError(new ApiError("NETWORK_ERROR", error.message));
    } else {
      onError(new ApiError("NETWORK_ERROR", "Unknown stream error"));
    }
  } finally {
    reader.releaseLock();
  }
}
