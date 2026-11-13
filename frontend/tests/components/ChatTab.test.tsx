import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { ApiError } from "../../src/api/errors";
import {
  createConversation,
  getConversation,
  getUsage,
  listConversations,
  sendMessage,
  type ChatEvent,
  type Citation,
  type Message,
} from "../../src/features/chat/api";
import { ChatTab } from "../../src/features/chat/ChatTab";
import {
  listDocuments,
  type DocumentItem,
} from "../../src/features/documents/api";
import i18n from "../../src/i18n";

jest.mock("../../src/features/chat/api", () => ({
  createConversation: jest.fn(),
  getConversation: jest.fn(),
  getUsage: jest.fn(),
  listConversations: jest.fn(),
  sendMessage: jest.fn(),
}));
jest.mock("../../src/features/documents/api", () => ({
  listDocuments: jest.fn(),
}));
const mockPush = jest.fn();
jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn() }),
}));

const docs = listDocuments as jest.MockedFunction<typeof listDocuments>;
const usage = getUsage as jest.MockedFunction<typeof getUsage>;
const list = listConversations as jest.MockedFunction<typeof listConversations>;
const detail = getConversation as jest.MockedFunction<typeof getConversation>;
const create = createConversation as jest.MockedFunction<
  typeof createConversation
>;
const send = sendMessage as jest.MockedFunction<typeof sendMessage>;

function doc(id: string, filename: string): DocumentItem {
  return {
    id,
    space_id: "s1",
    filename,
    size_bytes: 1,
    page_count: 3,
    status: "READY",
    error_code: null,
    created_at: "2026-11-13T00:00:00Z",
    updated_at: "2026-11-13T00:00:00Z",
  };
}

const conversation = {
  id: "c1",
  space_id: "s1",
  title: null,
  created_at: "2026-11-13T00:00:00Z",
  updated_at: "2026-11-13T00:00:00Z",
};

const citation: Citation = {
  index: 1,
  document_id: "d1",
  document_name: "Giải tích.pdf",
  page_start: 2,
  page_end: 2,
  snippet: "Đạo hàm là hệ số góc của tiếp tuyến.",
};

function message(overrides: Partial<Message>): Message {
  return {
    id: "m",
    conversation_id: "c1",
    role: "assistant",
    content: "",
    mode: "answer",
    status: "complete",
    error_code: null,
    citations: [],
    document_ids: null,
    created_at: "2026-11-13T00:00:00Z",
    ...overrides,
  };
}

const question = message({
  id: "q1",
  role: "user",
  mode: "question",
  content: "Đạo hàm là gì?",
});

function scripted(events: ChatEvent[]) {
  send.mockImplementation((_id, _q, _docs, onEvent) => {
    events.forEach(onEvent);
    return Promise.resolve();
  });
}

function renderTab() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ChatTab spaceId="s1" />
    </QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  await i18n.changeLanguage("vi");
  docs.mockResolvedValue({
    items: [doc("d1", "Giải tích.pdf"), doc("d2", "Đại số.pdf")],
    total_documents: 2,
    max_documents: 10,
  });
  usage.mockResolvedValue({
    daily_limit: 30,
    used_today: 2,
    remaining: 28,
    resets_at: "2026-11-13T17:00:00Z",
  });
  list.mockResolvedValue({ items: [] });
  create.mockResolvedValue(conversation);
  detail.mockResolvedValue({ ...conversation, messages: [] });
});

async function ask(text: string) {
  fireEvent.changeText(await screen.findByTestId("chat-input"), text);
  fireEvent.press(screen.getByTestId("chat-send"));
}

it("explains how to start when no document is ready", async () => {
  docs.mockResolvedValue({ items: [], total_documents: 0, max_documents: 10 });
  renderTab();
  expect(await screen.findByText("Chưa có tài liệu sẵn sàng")).toBeTruthy();
});

it("shows today's quota", async () => {
  renderTab();
  expect(await screen.findByText("Còn 28/30 câu hỏi hôm nay")).toBeTruthy();
});

it("creates a conversation, streams the answer and opens a citation", async () => {
  const answer = message({
    id: "a1",
    content: "Là hệ số góc của tiếp tuyến [1].",
    citations: [citation],
  });
  scripted([
    {
      type: "start",
      data: {
        user_message: question,
        assistant_message_id: "a1",
        mode: "answer",
      },
    },
    { type: "citations", data: { citations: [citation] } },
    { type: "delta", data: { text: "Là hệ số góc " } },
    { type: "delta", data: { text: "của tiếp tuyến [1]." } },
    { type: "done", data: { message: answer } },
  ]);
  detail.mockResolvedValue({ ...conversation, messages: [question, answer] });
  renderTab();

  await ask("Đạo hàm là gì?");

  expect(
    await screen.findByText("Là hệ số góc của tiếp tuyến [1]."),
  ).toBeTruthy();
  expect(create).toHaveBeenCalledWith("s1");
  expect(send).toHaveBeenCalledWith(
    "c1",
    "Đạo hàm là gì?",
    null,
    expect.any(Function),
  );
  expect(screen.getByText("Đạo hàm là gì?")).toBeTruthy();

  fireEvent.press(screen.getByTestId("citation-1"));
  expect(
    await screen.findByText("Đạo hàm là hệ số góc của tiếp tuyến."),
  ).toBeTruthy();
});

it("sends only the documents left selected", async () => {
  scripted([
    {
      type: "start",
      data: {
        user_message: question,
        assistant_message_id: "a1",
        mode: "not_found",
      },
    },
    { type: "done", data: { message: message({ mode: "not_found" }) } },
  ]);
  detail.mockResolvedValue({
    ...conversation,
    messages: [question, message({ id: "a1", mode: "not_found" })],
  });
  renderTab();

  fireEvent.press(await screen.findByTestId("chat-doc-d2"));
  await ask("Đạo hàm là gì?");

  await waitFor(() => expect(send).toHaveBeenCalled());
  expect(send.mock.calls[0]?.[2]).toEqual(["d1"]);
  expect(
    await screen.findByText(
      "Không tìm thấy nội dung này trong các tài liệu đã chọn.",
    ),
  ).toBeTruthy();
});

it("shows passages when AI is resting (retrieval only)", async () => {
  scripted([
    {
      type: "start",
      data: {
        user_message: question,
        assistant_message_id: "a1",
        mode: "retrieval_only",
      },
    },
    { type: "citations", data: { citations: [citation] } },
    {
      type: "done",
      data: {
        message: message({ mode: "retrieval_only", citations: [citation] }),
      },
    },
  ]);
  detail.mockResolvedValue({
    ...conversation,
    messages: [
      question,
      message({ id: "a1", mode: "retrieval_only", citations: [citation] }),
    ],
  });
  renderTab();

  await ask("Đạo hàm là gì?");

  expect(await screen.findByText(/AI đang tạm nghỉ/)).toBeTruthy();
  expect(screen.getByText("Đạo hàm là hệ số góc của tiếp tuyến.")).toBeTruthy();
});

it("keeps the question and explains when the daily quota is used up", async () => {
  send.mockRejectedValue(
    new ApiError("USER_QUOTA_EXCEEDED", "x", 429, {
      quotaRemaining: 0,
      quotaResetAt: new Date("2026-11-13T17:00:00Z"),
    }),
  );
  renderTab();

  await ask("Đạo hàm là gì?");

  expect(await screen.findByText(/hết lượt hỏi hôm nay/)).toBeTruthy();
  expect(screen.getByTestId("chat-input").props.value).toBe("Đạo hàm là gì?");
});

it("keeps the partial answer and the question when the stream breaks", async () => {
  scripted([
    {
      type: "start",
      data: {
        user_message: question,
        assistant_message_id: "a1",
        mode: "answer",
      },
    },
    { type: "delta", data: { text: "Đạo hàm là" } },
    {
      type: "error",
      data: { code: "AI_TEMPORARILY_UNAVAILABLE", message: "x" },
    },
  ]);
  detail
    .mockResolvedValueOnce({ ...conversation, messages: [] })
    .mockResolvedValue({
      ...conversation,
      messages: [
        question,
        message({ id: "a1", content: "Đạo hàm là", status: "partial" }),
      ],
    });
  renderTab();

  await ask("Đạo hàm là gì?");

  expect(await screen.findByText(/AI đang tạm nghỉ, vui lòng/)).toBeTruthy();
  expect(
    await screen.findByText("Câu trả lời bị ngắt giữa chừng."),
  ).toBeTruthy();
  expect(screen.getByTestId("chat-input").props.value).toBe("Đạo hàm là gì?");
});

it("marks citations of deleted documents", async () => {
  list.mockResolvedValue({ items: [conversation] });
  detail.mockResolvedValue({
    ...conversation,
    messages: [
      question,
      message({
        id: "a1",
        content: "Trả lời [1].",
        citations: [{ ...citation, document_id: null }],
      }),
    ],
  });
  renderTab();

  fireEvent.press(await screen.findByTestId("citation-1"));
  expect(await screen.findByText(/tài liệu đã xóa/)).toBeTruthy();
});

it("renders in English", async () => {
  await i18n.changeLanguage("en");
  renderTab();
  expect(await screen.findByText("28/30 questions left today")).toBeTruthy();
});

it("opens the cited page from a citation", async () => {
  list.mockResolvedValue({ items: [conversation] });
  detail.mockResolvedValue({
    ...conversation,
    messages: [
      question,
      message({ id: "a1", content: "Trả lời [1].", citations: [citation] }),
    ],
  });
  renderTab();

  fireEvent.press(await screen.findByTestId("citation-1"));
  fireEvent.press(await screen.findByTestId("citation-view-page"));

  expect(mockPush).toHaveBeenCalledWith({
    pathname: "/spaces/citation",
    params: { documentId: "d1", page: "2", highlight: citation.snippet },
  });
});

it("opens the history", async () => {
  renderTab();
  fireEvent.press(await screen.findByTestId("chat-history"));
  expect(mockPush).toHaveBeenCalledWith({
    pathname: "/spaces/history/[spaceId]",
    params: { spaceId: "s1" },
  });
});
