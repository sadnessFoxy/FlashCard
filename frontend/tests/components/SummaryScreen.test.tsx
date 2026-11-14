import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { ApiError } from "../../src/api/errors";
import { getUsage } from "../../src/features/chat/api";
import {
  listSections,
  summarizeSection,
  type SectionList,
} from "../../src/features/summaries/api";
import { SummaryScreen } from "../../src/features/summaries/SummaryScreen";
import i18n from "../../src/i18n";
import { usage } from "../fixtures/usage";

jest.mock("../../src/features/summaries/api", () => ({
  listSections: jest.fn(),
  summarizeSection: jest.fn(),
}));
jest.mock("../../src/features/chat/api", () => ({ getUsage: jest.fn() }));
const mockPush = jest.fn();
jest.mock("expo-router", () => ({
  useRouter: () => ({
    push: mockPush,
    back: jest.fn(),
    canGoBack: () => true,
    replace: jest.fn(),
  }),
}));

const list = listSections as jest.MockedFunction<typeof listSections>;
const make = summarizeSection as jest.MockedFunction<typeof summarizeSection>;
const getUsageMock = getUsage as jest.MockedFunction<typeof getUsage>;

const sections: SectionList = {
  document_id: "d1",
  filename: "Giải tích.pdf",
  items: [
    {
      id: "s1",
      position: 0,
      title: "Chương 1. Giới hạn",
      page_start: 1,
      page_end: 1,
      summary: {
        points: [{ text: "Giới hạn mô tả giá trị hàm số tiến tới.", page: 1 }],
        created_at: "2026-11-14T00:00:00Z",
      },
    },
    {
      id: "s2",
      position: 1,
      title: null,
      page_start: 2,
      page_end: 3,
      summary: null,
    },
  ],
};

function renderScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <SummaryScreen documentId="d1" />
    </QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  await i18n.changeLanguage("vi");
  getUsageMock.mockResolvedValue(usage());
  list.mockResolvedValue(sections);
});

it("shows saved summaries with page links", async () => {
  renderScreen();
  expect(await screen.findByText("Chương 1. Giới hạn · trang 1")).toBeTruthy();
  expect(screen.getByText("trang 2–3")).toBeTruthy();
  fireEvent.press(screen.getByText("trang 1"));
  expect(mockPush).toHaveBeenCalledWith({
    pathname: "/spaces/citation",
    params: {
      documentId: "d1",
      page: "1",
      highlight: "Giới hạn mô tả giá trị hàm số tiến tới.",
    },
  });
});

it("makes a missing summary on request", async () => {
  make.mockResolvedValue({
    points: [{ text: "Đạo hàm là hệ số góc.", page: 2 }],
    created_at: "2026-11-14T00:00:00Z",
  });
  renderScreen();

  fireEvent.press(await screen.findByTestId("section-summarize-s2"));

  await waitFor(() => expect(make).toHaveBeenCalledWith("d1", "s2"));
  expect(await screen.findByText("• Đạo hàm là hệ số góc.")).toBeTruthy();
});

it("explains when the summary quota is used up", async () => {
  make.mockRejectedValue(new ApiError("USER_QUOTA_EXCEEDED", "x", 429));
  renderScreen();
  fireEvent.press(await screen.findByTestId("section-summarize-s2"));
  expect(await screen.findByText(/hết lượt tóm tắt hôm nay/)).toBeTruthy();
});
