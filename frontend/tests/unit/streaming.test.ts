import { parseSse, readSse, type SseEvent } from "../../src/api/streaming";

it("parses complete events and keeps the unfinished tail", () => {
  const { events, rest } = parseSse(
    'event: start\ndata: {"mode":"answer"}\n\nevent: delta\ndata: {"text":"Xin "}\n\nevent: del',
  );
  expect(events).toEqual([
    { event: "start", data: { mode: "answer" } },
    { event: "delta", data: { text: "Xin " } },
  ]);
  expect(rest).toBe("event: del");
});

it("handles CRLF and skips malformed JSON", () => {
  const { events } = parseSse(
    'event: a\r\ndata: {bad\r\n\r\nevent: b\r\ndata: {"ok":true}\r\n\r\n',
  );
  expect(events).toEqual([{ event: "b", data: { ok: true } }]);
});

function streamOf(parts: string[]): Response {
  const encoder = new TextEncoder();
  let i = 0;
  const reader = {
    read: () =>
      Promise.resolve(
        i < parts.length
          ? { done: false, value: encoder.encode(parts[i++]) }
          : { done: true, value: undefined },
      ),
    releaseLock: () => undefined,
  };
  return { body: { getReader: () => reader } } as unknown as Response;
}

it("delivers events split across network chunks, in order", async () => {
  const seen: SseEvent[] = [];
  await readSse(
    streamOf([
      'event: delta\ndata: {"text":"Đạo',
      ' hàm"}\n\nevent: done\ndata: {"m":1}',
      "\n\n",
    ]),
    (e) => seen.push(e),
  );
  expect(seen).toEqual([
    { event: "delta", data: { text: "Đạo hàm" } },
    { event: "done", data: { m: 1 } },
  ]);
});

it("falls back to the full text when the body cannot stream", async () => {
  const seen: SseEvent[] = [];
  const response = {
    body: null,
    text: () => Promise.resolve('event: done\ndata: {"m":2}\n\n'),
  } as unknown as Response;
  await readSse(response, (e) => seen.push(e));
  expect(seen).toEqual([{ event: "done", data: { m: 2 } }]);
});
