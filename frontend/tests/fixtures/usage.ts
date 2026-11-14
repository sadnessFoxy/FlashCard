import type { Usage } from "../../src/features/chat/api";

type Counter = Usage["card_suggestions"];
const RESETS = "2026-11-14T17:00:00Z";

function counter(limit: number, used = 0): Counter {
  return {
    daily_limit: limit,
    used_today: used,
    remaining: limit - used,
    resets_at: RESETS,
  };
}

/** A full Usage payload; tests override only the counters they care about. */
export function usage(overrides: Partial<Usage> = {}): Usage {
  return {
    ...counter(30),
    card_suggestions: counter(10),
    quizzes: counter(5),
    summaries: counter(10),
    ...overrides,
  };
}

export { counter as usageCounter };
