import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react-native";

import { ApiError } from "../../src/api/errors";
import { getDocumentPage } from "../../src/features/documents/api";
import { CitationPageScreen } from "../../src/features/documents/CitationPageScreen";
import i18n from "../../src/i18n";

jest.mock("../../src/features/documents/api", () => ({
  getDocumentPage: jest.fn(),
}));
jest.mock("expo-router", () => ({
  useRouter: () => ({
    back: jest.fn(),
    canGoBack: () => true,
    replace: jest.fn(),
  }),
}));

const getPage = getDocumentPage as jest.MockedFunction<typeof getDocumentPage>;

function pageOf(page: number, paragraphs: string[]) {
  return {
    document_id: "d1",
    filename: "Giải tích.pdf",
    page,
    page_count: 3,
    paragraphs,
  };
}

function renderScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <CitationPageScreen
        documentId="d1"
        page={2}
        highlight="Đạo hàm là hệ số góc của tiếp tuyến."
      />
    </QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  await i18n.changeLanguage("vi");
});

it("opens the cited page and highlights the cited passage", async () => {
  getPage.mockResolvedValue(
    pageOf(2, ["Chương 2. Đạo hàm", "Đạo hàm là hệ số góc của tiếp tuyến."]),
  );
  renderScreen();

  expect(await screen.findByText("Trang 2/3")).toBeTruthy();
  expect(getPage).toHaveBeenCalledWith("d1", 2, expect.anything());
  expect(screen.getAllByTestId("citation-highlight")).toHaveLength(1);
});

it("moves between pages without highlighting other pages", async () => {
  getPage.mockImplementation((_id, n) =>
    Promise.resolve(pageOf(n, ["Đạo hàm là hệ số góc của tiếp tuyến."])),
  );
  renderScreen();

  fireEvent.press(await screen.findByTestId("citation-page-next"));

  expect(await screen.findByText("Trang 3/3")).toBeTruthy();
  expect(screen.queryByTestId("citation-highlight")).toBeNull();
});

it("explains a deleted document", async () => {
  getPage.mockRejectedValue(new ApiError("NOT_FOUND", "x", 404));
  renderScreen();
  expect(await screen.findByText(/tài liệu đã bị xóa/)).toBeTruthy();
});
