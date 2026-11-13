/**
 * Review session state as a pure reducer (screen 15, 16).
 * Cards graded "again" go back to the end of the session until they are remembered.
 */
import type { Flashcard } from "../flashcards/api";
import type { ReviewGrade } from "./api";

export interface SessionState {
  queue: Flashcard[];
  index: number;
  flipped: boolean;
  tally: Record<ReviewGrade, number>;
  /** Cards graded again or hard at least once, in first-seen order. */
  difficult: Flashcard[];
}

export type SessionAction =
  | { type: "start"; cards: Flashcard[] }
  | { type: "flip" }
  | { type: "grade"; grade: ReviewGrade };

export function startSession(cards: Flashcard[]): SessionState {
  return {
    queue: cards,
    index: 0,
    flipped: false,
    tally: { again: 0, hard: 0, good: 0, easy: 0 },
    difficult: [],
  };
}

export function currentCard(state: SessionState): Flashcard | null {
  return state.queue[state.index] ?? null;
}

export function isFinished(state: SessionState): boolean {
  return state.index >= state.queue.length;
}

export function sessionReducer(
  state: SessionState,
  action: SessionAction,
): SessionState {
  if (action.type === "start") return startSession(action.cards);
  const card = currentCard(state);
  if (!card) return state;
  switch (action.type) {
    case "flip":
      return { ...state, flipped: true };
    case "grade": {
      const { grade } = action;
      const struggled = grade === "again" || grade === "hard";
      return {
        ...state,
        queue: grade === "again" ? [...state.queue, card] : state.queue,
        index: state.index + 1,
        flipped: false,
        tally: { ...state.tally, [grade]: state.tally[grade] + 1 },
        difficult:
          struggled && !state.difficult.some((c) => c.id === card.id)
            ? [...state.difficult, card]
            : state.difficult,
      };
    }
  }
}
