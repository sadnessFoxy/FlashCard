import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import {
  deleteConversation,
  listConversations,
} from "../../src/features/chat/api";
import { ConversationHistoryScreen } from "../../src/features/chat/ConversationHistoryScreen";
import i18n from "../../src/i18n";

const mockReplace = jest.fn();
jest.mock("../../src/features/chat/api", () => ({
  listConversations: jest.fn(),
  deleteConversation: jest.fn(),
}));
jest.mock("expo-router", () => ({
  useRouter: () => ({ replace: mockReplace, push: jest.fn() }),
}));

const list = listConversations as jest.MockedFunction<typeof listConversations>;
const remove = deleteConversation as jest.MockedFunction<
  typeof deleteConversation
>;

const item = {
  id: "c1",
  space_id: "s1",
  title: "Đạo hàm là gì?",
  created_at: "2026-11-13T00:00:00Z",
  updated_at: "2026-11-13T00:00:00Z",
};

function renderScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ConversationHistoryScreen spaceId="s1" />
    </QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  await i18n.changeLanguage("vi");
});

it("shows the empty state", async () => {
  list.mockResolvedValue({ items: [] });
  renderScreen();
  expect(await screen.findByTestId("history-empty")).toBeTruthy();
});

it("reopens a conversation in the chat tab", async () => {
  list.mockResolvedValue({ items: [item] });
  renderScreen();

  fireEvent.press(await screen.findByTestId("history-open-c1"));

  expect(mockReplace).toHaveBeenCalledWith({
    pathname: "/spaces/[id]",
    params: { id: "s1", tab: "chat", conversation: "c1" },
  });
});

it("deletes after confirmation", async () => {
  list
    .mockResolvedValueOnce({ items: [item] })
    .mockResolvedValue({ items: [] });
  remove.mockResolvedValue(undefined);
  renderScreen();

  fireEvent.press(await screen.findByTestId("history-delete-c1"));
  expect(screen.getByText(/xóa vĩnh viễn/)).toBeTruthy();
  expect(remove).not.toHaveBeenCalled();
  fireEvent.press(screen.getByTestId("history-delete-confirm"));

  await waitFor(() => expect(remove).toHaveBeenCalledWith("c1"));
  expect(await screen.findByTestId("history-empty")).toBeTruthy();
});
