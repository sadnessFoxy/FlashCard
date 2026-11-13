import AsyncStorage from "@react-native-async-storage/async-storage";

import { NetworkError } from "../../src/api/errors";
import { submitReviews, type Review } from "../../src/features/reviews/api";
import {
  enqueueReview,
  flushReviews,
  pendingReviewCount,
} from "../../src/features/reviews/reviewQueue";

jest.mock("../../src/features/reviews/api", () => ({
  REVIEWS_PER_REQUEST: 2,
  submitReviews: jest.fn(),
}));

const submit = submitReviews as jest.MockedFunction<typeof submitReviews>;

function review(id: string): Review {
  return {
    id,
    card_id: "c",
    grade: "good",
    reviewed_at: "2026-11-13T00:00:00Z",
  };
}

function accepted(reviews: Review[]) {
  return {
    results: reviews.map((r) => ({
      id: r.id,
      card_id: r.card_id,
      status: "applied" as const,
      due_at: "2026-11-14T00:00:00Z",
      interval_days: 1,
    })),
  };
}

beforeEach(async () => {
  jest.clearAllMocks();
  await AsyncStorage.clear();
});

it("keeps reviews while offline and sends them later in batches", async () => {
  submit.mockRejectedValueOnce(new NetworkError("offline"));
  await enqueueReview(review("1"));
  await enqueueReview(review("2"));
  await enqueueReview(review("3"));

  const offline = await flushReviews();
  expect(offline).toEqual({ results: [], pending: 3 });

  submit.mockImplementation((batch) => Promise.resolve(accepted(batch)));
  const online = await flushReviews();

  expect(online.pending).toBe(0);
  expect(online.results.map((r) => r.id)).toEqual(["1", "2", "3"]);
  expect(submit.mock.calls.map(([batch]) => batch.map((r) => r.id))).toEqual([
    ["1", "2", "3"].slice(0, 2), // the failed offline attempt
    ["1", "2"],
    ["3"],
  ]);
  expect(await pendingReviewCount()).toBe(0);
});

it("survives an app restart (reviews are persisted)", async () => {
  await enqueueReview(review("1"));
  const stored = await AsyncStorage.getItem("flashcard.reviewQueue.v1");
  expect(JSON.parse(stored ?? "[]")).toHaveLength(1);
});
