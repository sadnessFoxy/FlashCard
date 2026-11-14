import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react-native";
import type { ReactNode } from "react";

import { ApiError } from "../../src/api/errors";
import {
  createSpace,
  deleteSpace,
  getSpace,
  listSpaces,
  renameSpace,
  type Space,
} from "../../src/features/spaces/api";
import { SpaceDetailScreen } from "../../src/features/spaces/SpaceDetailScreen";
import { SpacesScreen } from "../../src/features/spaces/SpacesScreen";
import i18n from "../../src/i18n";

jest.mock("../../src/features/spaces/api", () => ({
  listSpaces: jest.fn(),
  getSpace: jest.fn(),
  createSpace: jest.fn(),
  renameSpace: jest.fn(),
  deleteSpace: jest.fn(),
}));

// The detail screen embeds the documents tab; keep it offline and empty here.
jest.mock("../../src/features/documents/api", () => ({
  listDocuments: jest.fn(async () => ({
    items: [],
    total_documents: 0,
    max_documents: 10,
  })),
  uploadDocument: jest.fn(),
  hasCurrentAiConsent: jest.fn(async () => ({ ok: true, version: "v1" })),
  giveAiConsent: jest.fn(),
}));

const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock("../../src/features/chat/api", () => ({
  createConversation: jest.fn(),
  getConversation: jest.fn(),
  getUsage: jest.fn(),
  listConversations: jest.fn(),
  sendMessage: jest.fn(),
}));
jest.mock("../../src/features/quizzes/api", () => ({
  listQuizzes: jest.fn(async () => ({ items: [] })),
}));
jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
}));

const list = listSpaces as jest.MockedFunction<typeof listSpaces>;
const get = getSpace as jest.MockedFunction<typeof getSpace>;
const create = createSpace as jest.MockedFunction<typeof createSpace>;
const rename = renameSpace as jest.MockedFunction<typeof renameSpace>;
const remove = deleteSpace as jest.MockedFunction<typeof deleteSpace>;

function space(name: string, id = name.toLowerCase()): Space {
  return {
    id,
    name,
    created_at: "2026-11-10T00:00:00Z",
    updated_at: "2026-11-10T00:00:00Z",
  };
}

function renderWithQuery(ui: ReactNode) {
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
});

describe("SpacesScreen", () => {
  it("shows the empty state with a create button", async () => {
    list.mockResolvedValue([]);
    renderWithQuery(<SpacesScreen />);

    expect(await screen.findByText("Chưa có không gian nào")).toBeTruthy();
    expect(screen.getByText("Tạo không gian đầu tiên")).toBeTruthy();
  });

  it("lists spaces and opens one", async () => {
    list.mockResolvedValue([space("Giải tích 1", "a"), space("Hóa học", "b")]);
    renderWithQuery(<SpacesScreen />);

    fireEvent.press(await screen.findByText("Hóa học"));

    expect(screen.getByText("Giải tích 1")).toBeTruthy();
    expect(mockPush).toHaveBeenCalledWith({
      pathname: "/spaces/[id]",
      params: { id: "b" },
    });
  });

  it("shows an error with retry", async () => {
    list.mockRejectedValueOnce(new ApiError("INTERNAL_SERVER_ERROR", "x", 500));
    list.mockResolvedValueOnce([space("Sau khi thử lại")]);
    renderWithQuery(<SpacesScreen />);

    fireEvent.press(await screen.findByText("Thử lại"));

    expect(await screen.findByText("Sau khi thử lại")).toBeTruthy();
  });

  it("creates a space and puts it on top", async () => {
    list.mockResolvedValue([space("Cũ")]);
    create.mockResolvedValue(space("Mới"));
    renderWithQuery(<SpacesScreen />);

    fireEvent.press(await screen.findByTestId("spaces-create"));
    fireEvent.changeText(screen.getByTestId("space-name-input"), "  Mới  ");
    fireEvent.press(screen.getByTestId("space-name-save"));

    await waitFor(() => expect(create).toHaveBeenCalledWith("Mới"));
    const names = await screen.findAllByText(/^(Mới|Cũ)$/);
    expect(names.map((n) => n.props.children)).toEqual(["Mới", "Cũ"]);
  });

  it("validates the name locally and shows a duplicate from the server", async () => {
    list.mockResolvedValue([space("Cũ")]);
    create.mockRejectedValue(new ApiError("SPACE_NAME_TAKEN", "x", 409));
    renderWithQuery(<SpacesScreen />);

    fireEvent.press(await screen.findByTestId("spaces-create"));
    fireEvent.press(screen.getByTestId("space-name-save"));
    expect(screen.getByText("Hãy nhập tên không gian")).toBeTruthy();
    expect(create).not.toHaveBeenCalled();

    fireEvent.changeText(screen.getByTestId("space-name-input"), "cũ");
    fireEvent.press(screen.getByTestId("space-name-save"));
    expect(
      await screen.findByText("Bạn đã có một không gian trùng tên này"),
    ).toBeTruthy();
  });

  it("renames a space", async () => {
    list.mockResolvedValue([space("Cũ", "a")]);
    rename.mockResolvedValue(space("Mới", "a"));
    renderWithQuery(<SpacesScreen />);

    fireEvent.press(
      within(await screen.findByTestId("space-a")).getByText("Đổi tên"),
    );
    fireEvent.changeText(screen.getByTestId("space-name-input"), "Mới");
    fireEvent.press(screen.getByTestId("space-name-save"));

    expect(await screen.findByText("Mới")).toBeTruthy();
    expect(rename).toHaveBeenCalledWith("a", "Mới");
  });

  it("asks before deleting and warns that contents go too", async () => {
    list.mockResolvedValue([space("Tạm", "a")]);
    remove.mockResolvedValue(undefined);
    renderWithQuery(<SpacesScreen />);

    fireEvent.press(
      within(await screen.findByTestId("space-a")).getByText("Xóa"),
    );
    expect(screen.getByText(/sẽ bị xóa vĩnh viễn/)).toBeTruthy();
    expect(remove).not.toHaveBeenCalled();

    fireEvent.press(screen.getByTestId("space-delete-confirm"));

    await waitFor(() => expect(screen.queryByTestId("space-a")).toBeNull());
    expect(remove).toHaveBeenCalledWith("a");
  });

  it("cancelling the delete keeps the space", async () => {
    list.mockResolvedValue([space("Tạm", "a")]);
    renderWithQuery(<SpacesScreen />);

    fireEvent.press(
      within(await screen.findByTestId("space-a")).getByText("Xóa"),
    );
    fireEvent.press(screen.getByText("Hủy"));

    expect(remove).not.toHaveBeenCalled();
    expect(screen.getByTestId("space-a")).toBeTruthy();
  });

  it("renders in English", async () => {
    await i18n.changeLanguage("en");
    list.mockResolvedValue([]);
    renderWithQuery(<SpacesScreen />);

    expect(await screen.findByText("No spaces yet")).toBeTruthy();
  });
});

describe("SpaceDetailScreen", () => {
  it("shows the name and switches tabs", async () => {
    get.mockResolvedValue(space("Giải tích 1", "a"));
    renderWithQuery(<SpaceDetailScreen id="a" />);

    expect(await screen.findByTestId("space-title")).toBeTruthy();
    fireEvent.press(screen.getByText("Trắc nghiệm"));
    expect(await screen.findByTestId("quizzes-empty")).toBeTruthy();
  });

  it("handles a missing or foreign space", async () => {
    get.mockRejectedValue(new ApiError("NOT_FOUND", "x", 404));
    renderWithQuery(<SpaceDetailScreen id="nope" />);

    expect(
      await screen.findByText("Không gian này không tồn tại hoặc đã bị xóa."),
    ).toBeTruthy();
    fireEvent.press(screen.getByText("Về danh sách không gian"));
    expect(mockReplace).toHaveBeenCalledWith("/spaces");
  });

  it("returns to the list after deleting", async () => {
    get.mockResolvedValue(space("Tạm", "a"));
    remove.mockResolvedValue(undefined);
    renderWithQuery(<SpaceDetailScreen id="a" />);

    fireEvent.press(await screen.findByText("Xóa"));
    fireEvent.press(screen.getByTestId("space-delete-confirm"));

    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith("/spaces"));
  });
});
