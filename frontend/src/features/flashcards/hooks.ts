import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createDeck,
  createFlashcards,
  deleteDeck,
  deleteFlashcard,
  getDeck,
  listDecks,
  renameDeck,
  updateFlashcard,
  type NewFlashcard,
} from "./api";

export const deckKeys = {
  all: ["decks"] as const,
  inSpace: (spaceId: string) => ["decks", "space", spaceId] as const,
  detail: (id: string) => ["decks", "detail", id] as const,
};

export function useDecks(spaceId: string) {
  return useQuery({
    queryKey: deckKeys.inSpace(spaceId),
    queryFn: ({ signal }) => listDecks(spaceId, signal),
  });
}

export function useDeck(id: string) {
  return useQuery({
    queryKey: deckKeys.detail(id),
    queryFn: ({ signal }) => getDeck(id, signal),
    retry: false,
  });
}

/** Every deck change refreshes lists and details (counts depend on cards). */
function useInvalidateDecks() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: deckKeys.all });
}

export function useCreateDeck(spaceId: string) {
  const invalidate = useInvalidateDecks();
  return useMutation({
    mutationFn: (name: string) => createDeck(spaceId, name),
    onSuccess: invalidate,
  });
}

export function useRenameDeck(id: string) {
  const invalidate = useInvalidateDecks();
  return useMutation({
    mutationFn: (name: string) => renameDeck(id, name),
    onSuccess: invalidate,
  });
}

export function useDeleteDeck() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteDeck(id),
    onSuccess: (_r, id) => {
      qc.removeQueries({ queryKey: deckKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: deckKeys.all });
    },
  });
}

export function useAddCards() {
  const invalidate = useInvalidateDecks();
  return useMutation({
    mutationFn: ({
      deckId,
      cards,
    }: {
      deckId: string;
      cards: NewFlashcard[];
    }) => createFlashcards(deckId, cards),
    onSuccess: invalidate,
  });
}

export function useUpdateCard() {
  const invalidate = useInvalidateDecks();
  return useMutation({
    mutationFn: ({
      id,
      front,
      back,
    }: {
      id: string;
      front: string;
      back: string;
    }) => updateFlashcard(id, { front, back }),
    onSuccess: invalidate,
  });
}

export function useDeleteCard() {
  const invalidate = useInvalidateDecks();
  return useMutation({
    mutationFn: (id: string) => deleteFlashcard(id),
    onSuccess: invalidate,
  });
}
