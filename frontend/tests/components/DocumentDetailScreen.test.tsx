import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { ApiError } from "../../src/api/errors";
import {
  deleteDocument,
  getDocument,
  moveDocument,
  retryDocument,
  type DocumentItem,
} from "../../src/features/documents/api";
import { DocumentDetailScreen } from "../../src/features/documents/DocumentDetailScreen";
import { listSpaces } from "../../src/features/spaces/api";
import i18n from "../../src/i18n";

jest.mock("../../src/features/documents/api", () => ({
  getDocument: jest.fn(),
  retryDocument: jest.fn(),
  deleteDocument: jest.fn(),
  moveDocument: jest.fn(),
}));
jest.mock("../../src/features/spaces/api", () => ({ listSpaces: jest.fn() }));

const mockReplace = jest.fn();
const mockPush = jest.fn();
jest.mock("expo-router", () => ({
  useRouter: () => ({ replace: mockReplace, push: mockPush }),
}));

const get = getDocument as jest.MockedFunction<typeof getDocument>;
const retry = retryDocument as jest.MockedFunction<typeof retryDocument>;
const remove = deleteDocument as jest.MockedFunction<typeof deleteDocument>;
const move = moveDocument as jest.MockedFunction<typeof moveDocument>;
const spaces = listSpaces as jest.MockedFunction<typeof listSpaces>;

function doc(overrides: Partial<DocumentItem> = {}): DocumentItem {
  return {
    id: "d1",
    space_id: "s1",
    filename: "Giáo trình.pdf",
    size_bytes: 3 * 1024 * 1024,
    page_count: 12,
    status: "READY",
    error_code: null,
    created_at: "2026-11-12T00:00:00Z",
    updated_at: "2026-11-12T00:00:00Z",
    ...overrides,
  };
}

const SPACE = (id: string, name: string) => ({
  id,
  name,
  created_at: "2026-11-12T00:00:00Z",
  updated_at: "2026-11-12T00:00:00Z",
});

function renderScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <DocumentDetailScreen id="d1" />
    </QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  spaces.mockResolvedValue([SPACE("s1", "Giải tích"), SPACE("s2", "Hóa học")]);
  await i18n.changeLanguage("vi");
});

it("shows details and hides retry for a ready document", async () => {
  get.mockResolvedValue(doc());
  renderScreen();

  expect(await screen.findByTestId("document-title")).toBeTruthy();
  expect(screen.getByText("12 trang")).toBeTruthy();
  expect(screen.getByText("Dung lượng: 3.0 MB")).toBeTruthy();
  expect(screen.queryByTestId("document-retry")).toBeNull();
});

it("offers study shortcuts for a ready document only", async () => {
  get.mockResolvedValue(doc());
  const { unmount } = renderScreen();

  fireEvent.press(await screen.findByTestId("document-summaries"));
  expect(mockPush).toHaveBeenCalledWith({
    pathname: "/spaces/documents/summary/[documentId]",
    params: { documentId: doc().id },
  });
  unmount();

  get.mockResolvedValue(doc({ status: "PROCESSING" }));
  renderScreen();
  await screen.findByTestId("document-title");
  expect(screen.queryByTestId("document-summaries")).toBeNull();
});

it("retries a failed document", async () => {
  get.mockResolvedValue(
    doc({ status: "FAILED", error_code: "PROCESSING_FAILED" }),
  );
  retry.mockResolvedValue(doc({ status: "QUEUED" }));
  renderScreen();

  expect(await screen.findByText(/thất bại sau nhiều lần thử/)).toBeTruthy();
  fireEvent.press(screen.getByTestId("document-retry"));

  await waitFor(() => expect(retry).toHaveBeenCalledWith("d1"));
  expect(await screen.findByText("Đang chờ")).toBeTruthy();
});

it("deletes after confirmation and goes back to the space", async () => {
  get.mockResolvedValue(doc());
  remove.mockResolvedValue(undefined);
  renderScreen();

  fireEvent.press(await screen.findByTestId("document-delete"));
  expect(screen.getByText(/Lịch sử hỏi đáp vẫn được giữ/)).toBeTruthy();
  expect(remove).not.toHaveBeenCalled();
  fireEvent.press(screen.getByTestId("document-delete-confirm"));

  await waitFor(() =>
    expect(mockReplace).toHaveBeenCalledWith({
      pathname: "/spaces/[id]",
      params: { id: "s1" },
    }),
  );
  expect(remove).toHaveBeenCalledWith("d1");
});

it("moves to another space, never offering the current one", async () => {
  get.mockResolvedValue(doc());
  move.mockResolvedValue(doc({ space_id: "s2" }));
  renderScreen();

  fireEvent.press(await screen.findByTestId("document-move"));
  expect(screen.queryByTestId("move-to-s1")).toBeNull();
  fireEvent.press(await screen.findByTestId("move-to-s2"));

  await waitFor(() => expect(move).toHaveBeenCalledWith("d1", "s2"));
});

it("explains when there is no other space", async () => {
  spaces.mockResolvedValue([SPACE("s1", "Giải tích")]);
  get.mockResolvedValue(doc());
  renderScreen();

  fireEvent.press(await screen.findByTestId("document-move"));

  expect(await screen.findByText(/chưa có không gian nào khác/)).toBeTruthy();
});

it("handles a missing document", async () => {
  get.mockRejectedValue(new ApiError("NOT_FOUND", "x", 404));
  renderScreen();

  expect(
    await screen.findByText("Tài liệu này không tồn tại hoặc đã bị xóa."),
  ).toBeTruthy();
});
