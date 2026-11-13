import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useReducer, useState } from "react";

import { uuidv4 } from "../../utils/uuid";
import { deckKeys } from "../flashcards/hooks";
import { listDueCards, type ReviewGrade } from "./api";
import { enqueueReview, flushReviews } from "./reviewQueue";
import {
  currentCard,
  isFinished,
  sessionReducer,
  startSession,
} from "./session";

export interface SyncState {
  /** Reviews saved on this device but not yet on the server. */
  pending: number;
  /** Earliest next due time the server reported for this session's cards. */
  nextDueAt: Date | null;
}

/** Loads due cards once, plays the session, and syncs grades through the offline queue. */
export function useReviewSession(spaceId: string, deckId?: string) {
  const qc = useQueryClient();
  const due = useQuery({
    queryKey: ["reviews", "due", spaceId, deckId ?? "all"],
    queryFn: async ({ signal }) => {
      await flushReviews(); // earlier offline grades first, so they are not shown again
      return listDueCards(spaceId, deckId, signal);
    },
    staleTime: Infinity, // the session works on a snapshot
    gcTime: 0,
  });

  const [session, dispatch] = useReducer(sessionReducer, startSession([]));
  const [started, setStarted] = useState(false);
  const [sync, setSync] = useState<SyncState>({ pending: 0, nextDueAt: null });

  useEffect(() => {
    if (due.data && !started) {
      dispatch({ type: "start", cards: due.data.items });
      setStarted(true);
    }
  }, [due.data, started]);

  async function syncNow() {
    const outcome = await flushReviews();
    const dues = outcome.results
      .map((r) => (r.due_at ? new Date(r.due_at) : null))
      .filter((d): d is Date => d !== null);
    setSync((prev) => ({
      pending: outcome.pending,
      nextDueAt: [prev.nextDueAt, ...dues]
        .filter((d): d is Date => d !== null)
        .reduce<Date | null>((min, d) => (!min || d < min ? d : min), null),
    }));
    void qc.invalidateQueries({ queryKey: deckKeys.all });
  }

  function grade(value: ReviewGrade) {
    const card = currentCard(session);
    if (!card) return;
    dispatch({ type: "grade", grade: value });
    void enqueueReview({
      id: uuidv4(),
      card_id: card.id,
      grade: value,
      reviewed_at: new Date().toISOString(),
    }).then(syncNow);
  }

  return {
    due,
    session,
    card: currentCard(session),
    finished: started && isFinished(session),
    sync,
    flip: () => dispatch({ type: "flip" }),
    grade,
  };
}
