/**
 * Server-Sent Events reader for streamed answers (contract: POST /v1/conversations/{id}/messages).
 * Each event is `event: <name>` + `data: <JSON>` separated by a blank line.
 */

export interface SseEvent {
  event: string;
  data: unknown;
}

/** Split complete events off the buffer; the unfinished tail is returned as `rest`. */
export function parseSse(buffer: string): { events: SseEvent[]; rest: string } {
  const normalized = buffer.replace(/\r\n/g, "\n");
  const blocks = normalized.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: SseEvent[] = [];
  for (const block of blocks) {
    let event = "message";
    const data: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (data.length === 0) continue;
    try {
      events.push({ event, data: JSON.parse(data.join("\n")) });
    } catch {
      // ignore malformed events
    }
  }
  return { events, rest };
}

/** Feed every event of a streaming response to `onEvent`, as it arrives. */
export async function readSse(
  response: Response,
  onEvent: (event: SseEvent) => void,
): Promise<void> {
  const body = response.body;
  if (!body || typeof body.getReader !== "function") {
    // Fetch without streaming support: deliver everything at the end.
    const { events } = parseSse(`${await response.text()}\n\n`);
    events.forEach(onEvent);
    return;
  }
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSse(buffer);
      buffer = parsed.rest;
      parsed.events.forEach(onEvent);
    }
    parseSse(`${buffer}${decoder.decode()}\n\n`).events.forEach(onEvent);
  } finally {
    reader.releaseLock();
  }
}
