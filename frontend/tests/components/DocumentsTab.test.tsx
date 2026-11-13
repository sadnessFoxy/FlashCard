import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import * as DocumentPicker from "expo-document-picker";
import type { ReactNode } from "react";

import { ApiError, NetworkError } from "../../src/api/errors";
import {
  giveAiConsent,
  hasCurrentAiConsent,
  listDocuments,
  uploadDocument,
  type DocumentItem,
} from "../../src/features/documents/api";
import { DocumentsTab } from "../../src/features/documents/DocumentsTab";
import i18n from "../../src/i18n";
import { uuidv4 } from "../../src/utils/uuid";

jest.mock("../../src/features/documents/api", () => ({
  listDocuments: jest.fn(),
  uploadDocument: jest.fn(),
  hasCurrentAiConsent: jest.fn(),
  giveAiConsent: jest.fn(),
}));
jest.mock("expo-document-picker", () => ({ getDocumentAsync: jest.fn() }));

const list = listDocuments as jest.MockedFunction<typeof listDocuments>;
const upload = uploadDocument as jest.MockedFunction<typeof uploadDocument>;
const consentStatus = hasCurrentAiConsent as jest.MockedFunction<
  typeof hasCurrentAiConsent
>;
const consent = giveAiConsent as jest.MockedFunction<typeof giveAiConsent>;
const picker = DocumentPicker.getDocumentAsync as jest.MockedFunction<
  typeof DocumentPicker.getDocumentAsync
>;

function doc(overrides: Partial<DocumentItem> = {}): DocumentItem {
  return {
    id: "d1",
    space_id: "s1",
    filename: "Giáo trình.pdf",
    size_bytes: 1000,
    page_count: 12,
    status: "READY",
    error_code: null,
    created_at: "2026-11-12T00:00:00Z",
    updated_at: "2026-11-12T00:00:00Z",
    ...overrides,
  };
}

function page(items: DocumentItem[], total = items.length, max = 10) {
  return { items, total_documents: total, max_documents: max };
}

function picked() {
  picker.mockResolvedValue({
    canceled: false,
    assets: [
      {
        name: "Bài giảng.pdf",
        uri: "file:///b.pdf",
        size: 2048,
        mimeType: "application/pdf",
        lastModified: 0,
      },
    ],
  } as unknown as DocumentPicker.DocumentPickerResult);
}

function renderTab(ui: ReactNode = <DocumentsTab spaceId="s1" />) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  consentStatus.mockResolvedValue({ ok: true, version: "v1" });
  await i18n.changeLanguage("vi");
});

it("shows the empty state", async () => {
  list.mockResolvedValue(page([]));
  renderTab();

  expect(await screen.findByText("Chưa có tài liệu nào")).toBeTruthy();
  expect(screen.getByText("0/10 tài liệu")).toBeTruthy();
});

it("labels each status and explains failures", async () => {
  list.mockResolvedValue(
    page([
      doc({ id: "a", status: "READY" }),
      doc({ id: "b", status: "PROCESSING" }),
      doc({ id: "c", status: "FAILED", error_code: "NO_TEXT_LAYER" }),
      doc({ id: "d", status: "PAUSED_QUOTA" }),
    ]),
  );
  renderTab();

  expect(await screen.findByText("Sẵn sàng")).toBeTruthy();
  expect(screen.getByText("Đang xử lý")).toBeTruthy();
  expect(screen.getByText(/Tài liệu scan/)).toBeTruthy();
  expect(screen.getByText("Tạm dừng")).toBeTruthy();
  expect(screen.getByText(/tự xử lý tiếp/)).toBeTruthy();
});

it("asks for consent before the first upload, then uploads", async () => {
  consentStatus.mockResolvedValue({ ok: false, version: "v1" });
  consent.mockResolvedValue({
    kind: "ai_processing",
    version: "v1",
    created_at: "x",
  });
  const uploaded = doc({
    id: "new",
    status: "QUEUED",
    filename: "Bài giảng.pdf",
  });
  list.mockResolvedValueOnce(page([])).mockResolvedValue(page([uploaded]));
  picked();
  upload.mockResolvedValue(uploaded);
  renderTab();

  fireEvent.press(await screen.findByTestId("documents-upload"));
  expect(screen.getByText(/gửi cho Google/)).toBeTruthy();
  expect(picker).not.toHaveBeenCalled();

  fireEvent.press(screen.getByTestId("documents-consent-accept"));

  await waitFor(() => expect(upload).toHaveBeenCalledTimes(1));
  expect(consent).toHaveBeenCalledWith("v1");
  expect(await screen.findByText("Bài giảng.pdf")).toBeTruthy();
});

it("cancelling consent uploads nothing", async () => {
  consentStatus.mockResolvedValue({ ok: false, version: "v1" });
  list.mockResolvedValue(page([]));
  renderTab();

  fireEvent.press(await screen.findByTestId("documents-upload"));
  fireEvent.press(screen.getByText("Hủy"));

  expect(consent).not.toHaveBeenCalled();
  expect(picker).not.toHaveBeenCalled();
});

it("retry after a network error reuses the same Idempotency-Key", async () => {
  list.mockResolvedValue(page([]));
  picked();
  upload.mockRejectedValueOnce(new NetworkError("offline"));
  upload.mockResolvedValueOnce(doc({ id: "new", status: "QUEUED" }));
  renderTab();

  fireEvent.press(await screen.findByTestId("documents-upload"));
  expect(await screen.findByText(/không bị tạo trùng/)).toBeTruthy();
  fireEvent.press(screen.getByText("Thử lại"));

  await waitFor(() => expect(upload).toHaveBeenCalledTimes(2));
  const [first, second] = upload.mock.calls;
  expect(second?.[2]).toBe(first?.[2]);
});

it("shows server limits from error details", async () => {
  list.mockResolvedValue(page([]));
  picked();
  upload.mockRejectedValue(
    new ApiError("TOO_MANY_PAGES", "x", 422, { maxPages: 200 }),
  );
  renderTab();

  fireEvent.press(await screen.findByTestId("documents-upload"));

  expect(
    await screen.findByText("Tài liệu quá dài (tối đa 200 trang)."),
  ).toBeTruthy();
});

it("rejects oversized files before uploading", async () => {
  list.mockResolvedValue(page([]));
  picker.mockResolvedValue({
    canceled: false,
    assets: [
      {
        name: "big.pdf",
        uri: "file:///big.pdf",
        size: 25 * 1024 * 1024,
        mimeType: "application/pdf",
        lastModified: 0,
      },
    ],
  } as unknown as DocumentPicker.DocumentPickerResult);
  renderTab();

  fireEvent.press(await screen.findByTestId("documents-upload"));

  expect(await screen.findByText("File quá lớn (tối đa 20 MB).")).toBeTruthy();
  expect(upload).not.toHaveBeenCalled();
});

it("disables upload at the document limit", async () => {
  list.mockResolvedValue(page([doc()], 10, 10));
  renderTab();

  const button = await screen.findByTestId("documents-upload");

  expect(button.props.accessibilityState.disabled).toBe(true);
  expect(screen.getByText(/là mức tối đa/)).toBeTruthy();
});

it("renders in English", async () => {
  await i18n.changeLanguage("en");
  list.mockResolvedValue(page([doc({ status: "QUEUED" })]));
  renderTab();

  expect(await screen.findByText("Waiting")).toBeTruthy();
});

it("generates RFC 4122 v4 ids", () => {
  const ids = new Set(Array.from({ length: 50 }, uuidv4));
  expect(ids.size).toBe(50);
  for (const id of ids) {
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
  }
});
