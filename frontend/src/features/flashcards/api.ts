import { api } from "../../api/client";
import type { components } from "../../api/generated/schema";

type Schemas = components["schemas"];
export type Deck = Schemas["Deck"];
export type DeckDetail = Schemas["DeckDetail"];
export type DeckList = Schemas["DeckList"];
export type Flashcard = Schemas["Flashcard"];
export type NewFlashcard = Schemas["NewFlashcard"];
export type CardSource = Schemas["CardSource"];
export type Suggestion = Schemas["Suggestion"];
export type SuggestionRequest = Schemas["SuggestionRequest"];

const deckPath = (id: string) => `/v1/decks/${encodeURIComponent(id)}`;
const cardPath = (id: string) => `/v1/flashcards/${encodeURIComponent(id)}`;

export function listDecks(spaceId: string, signal?: AbortSignal) {
  return api.get<DeckList>(
    `/v1/decks?space_id=${encodeURIComponent(spaceId)}`,
    signal ? { signal } : {},
  );
}

export function getDeck(id: string, signal?: AbortSignal) {
  return api.get<DeckDetail>(deckPath(id), signal ? { signal } : {});
}

export function createDeck(spaceId: string, name: string) {
  return api.post<Deck>("/v1/decks", { space_id: spaceId, name });
}

export function renameDeck(id: string, name: string) {
  return api.patch<Deck>(deckPath(id), { name });
}

export function deleteDeck(id: string) {
  return api.delete<void>(deckPath(id));
}

export function createFlashcards(deckId: string, cards: NewFlashcard[]) {
  return api.post<{ items: Flashcard[] }>("/v1/flashcards", {
    deck_id: deckId,
    cards,
  });
}

export function updateFlashcard(
  id: string,
  changes: { front?: string; back?: string },
) {
  return api.patch<Flashcard>(cardPath(id), changes);
}

export function deleteFlashcard(id: string) {
  return api.delete<void>(cardPath(id));
}

export function suggestFlashcards(request: SuggestionRequest) {
  // Generation takes a few seconds; allow more than the default timeout.
  return api.post<{ items: Suggestion[] }>(
    "/v1/flashcards/suggestions",
    request,
    { timeoutMs: 90_000 },
  );
}
