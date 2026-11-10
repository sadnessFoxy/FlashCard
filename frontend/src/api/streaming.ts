/**
 * Xử lý Server-Sent Events (SSE) cho hỏi đáp streaming.
 * Mỗi event là một JSON chunk theo contract/openapi.yaml.
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
 * Đọc SSE stream từ response và gọi callback cho mỗi chunk.
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
            // Bỏ qua JSON parse lỗi từng dòng
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
