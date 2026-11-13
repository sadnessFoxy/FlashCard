import AsyncStorage from "@react-native-async-storage/async-storage";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { NetworkError } from "../../src/api/errors";
import type { Flashcard } from "../../src/features/flashcards/api";
import { listDueCards, submitReviews } from "../../src/features/reviews/api";
import { ReviewScreen } from "../../src/features/reviews/ReviewScreen";
import i18n from "../../src/i18n";

jest.mock("../../src/features/reviews/api", () => ({
  REVIEWS_PER_REQUEST: 100,
  listDueCards: jest.fn(),
  submitReviews: jest.fn(),
}));
jest.mock("expo-router", () => ({
  useRouter: () => ({
    back: jest.fn(),
    canGoBack: () => true,
    replace: jest.fn(),
  }),
}));

const due = listDueCards as jest.MockedFunction<typeof listDueCards>;
const submit = submitReviews as jest.MockedFunction<typeof submitReviews>;

function card(id: string): Flashcard {
  return {
    id,
    deck_id: "k",
    front: `Câu hỏi ${id}`,
    back: `Đáp án ${id}`,
    origin: "manual",
    source: null,
    due_at: "2026-11-13T00:00:00Z",
    created_at: "2026-11-13T00:00:00Z",
    updated_at: "2026-11-13T00:00:00Z",
  };
}

function renderScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ReviewScreen spaceId="s1" />
    </QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  await AsyncStorage.clear();
  await i18n.changeLanguage("vi");
  submit.mockImplementation((reviews) =>
    Promise.resolve({
      results: reviews.map((r) => ({
        id: r.id,
        card_id: r.card_id,
        status: "applied" as const,
        due_at: "2026-11-14T08:00:00Z",
        interval_days: 1,
      })),
    }),
  );
});

it("says when nothing is due", async () => {
  due.mockResolvedValue({ items: [], total_due: 0 });
  renderScreen();
  expect(await screen.findByTestId("review-nothing-due")).toBeTruthy();
});

it("flips, grades every card and shows the summary", async () => {
  due.mockResolvedValue({ items: [card("1"), card("2")], total_due: 2 });
  renderScreen();

  expect(await screen.findByText("Câu hỏi 1")).toBeTruthy();
  expect(screen.queryByTestId("review-back")).toBeNull();
  fireEvent.press(screen.getByTestId("review-flip"));
  expect(screen.getByText("Đáp án 1")).toBeTruthy();
  fireEvent.press(screen.getByTestId("review-grade-again"));

  expect(screen.getByText("Thẻ 2/3")).toBeTruthy(); // the forgotten card comes back
  fireEvent.press(screen.getByTestId("review-flip"));
  fireEvent.press(screen.getByTestId("review-grade-good"));
  fireEvent.press(screen.getByTestId("review-flip"));
  fireEvent.press(screen.getByTestId("review-grade-good"));

  expect(await screen.findByTestId("review-summary")).toBeTruthy();
  expect(screen.getByText("Đã ôn 3 lượt")).toBeTruthy();
  expect(screen.getByText("• Câu hỏi 1")).toBeTruthy();
  // Quick grades may share one request; every grade reaches the server once, in order.
  const sent = () =>
    submit.mock.calls.flatMap(([batch]) => batch.map((r) => r.grade));
  await waitFor(() => expect(sent()).toEqual(["again", "good", "good"]));
  expect(await screen.findByTestId("review-next-due")).toBeTruthy();
});

it("keeps grades on the device while offline", async () => {
  due.mockResolvedValue({ items: [card("1")], total_due: 1 });
  submit.mockRejectedValue(new NetworkError("offline"));
  renderScreen();

  fireEvent.press(await screen.findByTestId("review-flip"));
  fireEvent.press(screen.getByTestId("review-grade-easy"));

  expect(await screen.findByText(/1 kết quả đang lưu trên máy/)).toBeTruthy();
});
