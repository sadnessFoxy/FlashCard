import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import type { ReactNode } from "react";

import { ApiError } from "../../src/api/errors";
import { listDocuments } from "../../src/features/documents/api";
import {
  createDeck,
  createFlashcards,
  deleteFlashcard,
  getDeck,
  listDecks,
  suggestFlashcards,
  updateFlashcard,
  type DeckDetail,
  type Flashcard,
} from "../../src/features/flashcards/api";
import { DeckDetailScreen } from "../../src/features/flashcards/DeckDetailScreen";
import { DecksTab } from "../../src/features/flashcards/DecksTab";
import { GenerateCardsScreen } from "../../src/features/flashcards/GenerateCardsScreen";
import i18n from "../../src/i18n";

jest.mock("../../src/features/flashcards/api", () => ({
  listDecks: jest.fn(),
  getDeck: jest.fn(),
  createDeck: jest.fn(),
  renameDeck: jest.fn(),
  deleteDeck: jest.fn(),
  createFlashcards: jest.fn(),
  updateFlashcard: jest.fn(),
  deleteFlashcard: jest.fn(),
  suggestFlashcards: jest.fn(),
}));
jest.mock("../../src/features/documents/api", () => ({
  listDocuments: jest.fn(),
}));
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock("expo-router", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: jest.fn(),
    canGoBack: () => true,
  }),
}));

const decks = listDecks as jest.MockedFunction<typeof listDecks>;
const deck = getDeck as jest.MockedFunction<typeof getDeck>;
const create = createDeck as jest.MockedFunction<typeof createDeck>;
const addCards = createFlashcards as jest.MockedFunction<
  typeof createFlashcards
>;
const update = updateFlashcard as jest.MockedFunction<typeof updateFlashcard>;
const removeCard = deleteFlashcard as jest.MockedFunction<
  typeof deleteFlashcard
>;
const suggest = suggestFlashcards as jest.MockedFunction<
  typeof suggestFlashcards
>;
const docs = listDocuments as jest.MockedFunction<typeof listDocuments>;

const NOW = "2026-11-13T00:00:00Z";
const deckInfo = {
  id: "k1",
  space_id: "s1",
  name: "Đạo hàm",
  card_count: 1,
  due_count: 1,
  created_at: NOW,
  updated_at: NOW,
};

function card(overrides: Partial<Flashcard> = {}): Flashcard {
  return {
    id: "c1",
    deck_id: "k1",
    front: "Đạo hàm là gì?",
    back: "Hệ số góc tiếp tuyến",
    origin: "ai",
    source: { document_id: "d1", document_name: "Giải tích.pdf", page: 2 },
    due_at: NOW,
    created_at: NOW,
    updated_at: NOW,
    ...overrides,
  };
}

function wrap(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  await i18n.changeLanguage("vi");
  docs.mockResolvedValue({
    items: [
      {
        id: "d1",
        space_id: "s1",
        filename: "Giải tích.pdf",
        file_kind: "pdf",
        text_source: "text",
        size_bytes: 1,
        page_count: 3,
        status: "READY",
        error_code: null,
        created_at: NOW,
        updated_at: NOW,
      },
    ],
    total_documents: 1,
    max_documents: 10,
  });
});

describe("DecksTab", () => {
  it("shows the empty state", async () => {
    decks.mockResolvedValue({ items: [] });
    wrap(<DecksTab spaceId="s1" />);
    expect(await screen.findByTestId("decks-empty")).toBeTruthy();
  });

  it("lists decks with counts and creates a deck", async () => {
    decks.mockResolvedValue({
      items: [{ ...deckInfo, card_count: 5, due_count: 2 }],
    });
    create.mockResolvedValue({ ...deckInfo, id: "k2", name: "Tích phân" });
    wrap(<DecksTab spaceId="s1" />);

    expect(await screen.findByText("5 thẻ · 2 thẻ cần ôn")).toBeTruthy();
    fireEvent.press(screen.getByTestId("decks-create"));
    fireEvent.changeText(
      screen.getByTestId("deck-name-input"),
      "  Tích   phân ",
    );
    fireEvent.press(screen.getByTestId("deck-name-save"));

    await waitFor(() => expect(create).toHaveBeenCalledWith("s1", "Tích phân"));
    expect(mockPush).toHaveBeenCalledWith({
      pathname: "/spaces/decks/[deckId]",
      params: { deckId: "k2" },
    });
  });
});

describe("DeckDetailScreen", () => {
  const detail: DeckDetail = { ...deckInfo, cards: [card()] };

  it("shows cards with their source and opens the cited page", async () => {
    deck.mockResolvedValue(detail);
    wrap(<DeckDetailScreen deckId="k1" />);

    fireEvent.press(await screen.findByText("Giải tích.pdf · trang 2"));
    expect(mockPush).toHaveBeenCalledWith({
      pathname: "/spaces/citation",
      params: {
        documentId: "d1",
        page: "2",
        highlight: "Hệ số góc tiếp tuyến",
      },
    });
  });

  it("adds a card by hand and validates both sides", async () => {
    deck.mockResolvedValue({ ...detail, cards: [] });
    addCards.mockResolvedValue({ items: [card()] });
    wrap(<DeckDetailScreen deckId="k1" />);

    fireEvent.press(await screen.findByTestId("deck-add-card"));
    fireEvent.changeText(screen.getByTestId("card-front"), "Mặt trước");
    fireEvent.press(screen.getByTestId("card-save"));
    expect(
      await screen.findByText("Nhập cả mặt trước và mặt sau."),
    ).toBeTruthy();

    fireEvent.changeText(screen.getByTestId("card-back"), "Mặt sau");
    fireEvent.press(screen.getByTestId("card-save"));
    await waitFor(() =>
      expect(addCards).toHaveBeenCalledWith("k1", [
        { front: "Mặt trước", back: "Mặt sau", origin: "manual" },
      ]),
    );
  });

  it("edits and deletes a card", async () => {
    deck.mockResolvedValue(detail);
    update.mockResolvedValue(card({ back: "Mới" }));
    removeCard.mockResolvedValue(undefined);
    wrap(<DeckDetailScreen deckId="k1" />);

    fireEvent.press(await screen.findByTestId("card-edit-c1"));
    fireEvent.changeText(screen.getByTestId("card-back"), "Mới");
    fireEvent.press(screen.getByTestId("card-save"));
    await waitFor(() =>
      expect(update).toHaveBeenCalledWith("c1", {
        front: "Đạo hàm là gì?",
        back: "Mới",
      }),
    );

    fireEvent.press(screen.getByTestId("card-delete-c1"));
    fireEvent.press(screen.getByTestId("card-delete-dialog-confirm"));
    await waitFor(() => expect(removeCard).toHaveBeenCalledWith("c1"));
  });

  it("explains a missing deck", async () => {
    deck.mockRejectedValue(new ApiError("NOT_FOUND", "x", 404));
    wrap(<DeckDetailScreen deckId="k1" />);
    expect(await screen.findByTestId("deck-missing")).toBeTruthy();
  });
});

describe("GenerateCardsScreen", () => {
  const suggestions = {
    items: [
      {
        front: "Q1",
        back: "A1",
        source: { document_id: "d1", document_name: "Giải tích.pdf", page: 2 },
      },
      { front: "Q2", back: "A2", source: null },
    ],
  };

  it("suggests cards; the learner edits, skips one and saves the rest", async () => {
    decks.mockResolvedValue({ items: [deckInfo] });
    suggest.mockResolvedValue(suggestions);
    addCards.mockResolvedValue({ items: [card()] });
    wrap(<GenerateCardsScreen spaceId="s1" deckId="k1" />);

    fireEvent.changeText(await screen.findByTestId("generate-page-from"), "2");
    fireEvent.press(screen.getByTestId("generate-suggest"));
    await waitFor(() =>
      expect(suggest).toHaveBeenCalledWith({
        space_id: "s1",
        source: {
          type: "document",
          document_id: "d1",
          page_start: 2,
          page_end: null,
        },
        count: 10,
      }),
    );

    fireEvent.changeText(await screen.findByDisplayValue("A1"), "A1 sửa");
    fireEvent.press(screen.getByTestId("suggestion-toggle-1"));
    fireEvent.press(screen.getByText("Lưu 1 thẻ"));

    await waitFor(() =>
      expect(addCards).toHaveBeenCalledWith("k1", [
        {
          front: "Q1",
          back: "A1 sửa",
          origin: "ai",
          source: { document_id: "d1", page: 2 },
        },
      ]),
    );
    expect(mockReplace).toHaveBeenCalledWith({
      pathname: "/spaces/decks/[deckId]",
      params: { deckId: "k1" },
    });
  });

  it("from a Q&A answer, saves into a new deck", async () => {
    decks.mockResolvedValue({ items: [] });
    suggest.mockResolvedValue(suggestions);
    create.mockResolvedValue({ ...deckInfo, id: "k9" });
    addCards.mockResolvedValue({ items: [card()] });
    wrap(<GenerateCardsScreen spaceId="s1" messageId="m1" />);

    fireEvent.press(await screen.findByTestId("generate-suggest"));
    await waitFor(() =>
      expect(suggest.mock.calls[0]?.[0].source).toEqual({
        type: "message",
        message_id: "m1",
      }),
    );
    fireEvent.press(await screen.findByText("Lưu 2 thẻ"));

    await waitFor(() =>
      expect(create).toHaveBeenCalledWith("s1", "Bộ thẻ mới"),
    );
    expect(addCards.mock.calls[0]?.[0]).toBe("k9");
  });

  it("explains when the AI quota is used up", async () => {
    decks.mockResolvedValue({ items: [deckInfo] });
    suggest.mockRejectedValue(new ApiError("USER_QUOTA_EXCEEDED", "x", 429));
    wrap(<GenerateCardsScreen spaceId="s1" deckId="k1" />);

    await screen.findByTestId("generate-doc-d1"); // documents loaded: the button is enabled
    fireEvent.press(screen.getByTestId("generate-suggest"));

    expect(await screen.findByText(/hết lượt tạo thẻ/)).toBeTruthy();
    expect(screen.getByText(/thêm thẻ bằng tay/)).toBeTruthy();
  });
});
