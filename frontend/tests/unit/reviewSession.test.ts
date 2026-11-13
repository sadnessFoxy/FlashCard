import type { Flashcard } from "../../src/features/flashcards/api";
import {
  currentCard,
  isFinished,
  sessionReducer,
  startSession,
} from "../../src/features/reviews/session";

function card(id: string): Flashcard {
  return {
    id,
    deck_id: "k",
    front: `F${id}`,
    back: `B${id}`,
    origin: "manual",
    source: null,
    due_at: "2026-11-13T00:00:00Z",
    created_at: "2026-11-13T00:00:00Z",
    updated_at: "2026-11-13T00:00:00Z",
  };
}

it("flips, grades and finishes", () => {
  let s = startSession([card("1"), card("2")]);
  s = sessionReducer(s, { type: "flip" });
  expect(s.flipped).toBe(true);
  s = sessionReducer(s, { type: "grade", grade: "good" });
  expect(currentCard(s)?.id).toBe("2");
  expect(s.flipped).toBe(false);
  s = sessionReducer(s, { type: "grade", grade: "easy" });
  expect(isFinished(s)).toBe(true);
  expect(s.tally).toEqual({ again: 0, hard: 0, good: 1, easy: 1 });
});

it("brings forgotten cards back at the end and lists hard cards once", () => {
  let s = startSession([card("1"), card("2")]);
  s = sessionReducer(s, { type: "grade", grade: "again" });
  s = sessionReducer(s, { type: "grade", grade: "hard" });
  expect(currentCard(s)?.id).toBe("1"); // came back
  s = sessionReducer(s, { type: "grade", grade: "again" });
  expect(currentCard(s)?.id).toBe("1");
  s = sessionReducer(s, { type: "grade", grade: "good" });
  expect(isFinished(s)).toBe(true);
  expect(s.difficult.map((c) => c.id)).toEqual(["1", "2"]);
  expect(s.tally.again).toBe(2);
});

it("ignores actions once finished", () => {
  const done = startSession([]);
  expect(sessionReducer(done, { type: "grade", grade: "good" })).toBe(done);
});
