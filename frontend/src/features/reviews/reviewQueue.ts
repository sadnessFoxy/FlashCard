/**
 * Graded reviews waiting to reach the server (U12: works offline, syncs later).
 * Each review has a client-made id, so sending one twice is harmless: the server
 * answers "duplicate". Review grades are not secrets, so AsyncStorage is fine here (R12
 * only forbids it for tokens).
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

import { ApiError } from "../../api/errors";
import {
  REVIEWS_PER_REQUEST,
  submitReviews,
  type Review,
  type ReviewResult,
} from "./api";

const STORAGE_KEY = "flashcard.reviewQueue.v1";

async function load(): Promise<Review[]> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Review[]) : [];
  } catch {
    return [];
  }
}

async function save(queue: Review[]): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
}

// Queue writes and flushes run one at a time so nothing is lost or sent twice at once.
let chain: Promise<unknown> = Promise.resolve();
function serial<T>(task: () => Promise<T>): Promise<T> {
  const next = chain.then(task, task);
  chain = next.catch(() => undefined);
  return next;
}

export function enqueueReview(review: Review): Promise<void> {
  return serial(async () => save([...(await load()), review]));
}

export function pendingReviewCount(): Promise<number> {
  return serial(async () => (await load()).length);
}

export interface FlushOutcome {
  results: ReviewResult[];
  /** Reviews still waiting (the network was unavailable). */
  pending: number;
}

/** Send queued reviews in batches; stops at the first network failure and keeps the rest. */
export function flushReviews(): Promise<FlushOutcome> {
  return serial(async () => {
    let queue = await load();
    const results: ReviewResult[] = [];
    while (queue.length > 0) {
      const batch = queue.slice(0, REVIEWS_PER_REQUEST);
      try {
        results.push(...(await submitReviews(batch)).results);
      } catch (error) {
        if (
          error instanceof ApiError &&
          !error.isNetworkError &&
          error.statusCode !== 401
        ) {
          // The server refused the batch for good (e.g. invalid data): drop it, don't loop.
          queue = queue.slice(batch.length);
          await save(queue);
          continue;
        }
        break;
      }
      queue = queue.slice(batch.length);
      await save(queue);
    }
    return { results, pending: queue.length };
  });
}
