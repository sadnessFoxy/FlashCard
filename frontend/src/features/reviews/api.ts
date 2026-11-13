import { api } from "../../api/client";
import type { components } from "../../api/generated/schema";

type Schemas = components["schemas"];
export type Review = Schemas["Review"];
export type ReviewGrade = Schemas["ReviewGrade"];
export type ReviewResult = Schemas["ReviewResult"];
export type DueCards = Schemas["DueCards"];

export const REVIEWS_PER_REQUEST = 100;

export function listDueCards(
  spaceId: string,
  deckId?: string,
  signal?: AbortSignal,
): Promise<DueCards> {
  const query = new URLSearchParams({ space_id: spaceId, limit: "100" });
  if (deckId) query.set("deck_id", deckId);
  return api.get<DueCards>(
    `/v1/reviews/due?${query.toString()}`,
    signal ? { signal } : {},
  );
}

export function submitReviews(
  reviews: Review[],
): Promise<{ results: ReviewResult[] }> {
  return api.post<{ results: ReviewResult[] }>("/v1/reviews", { reviews });
}
