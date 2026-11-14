import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { ApiError } from "../../src/api/errors";
import type { User } from "../../src/features/auth/api";
import { useAuthStore } from "../../src/features/auth/useAuthStore";
import { getUsage } from "../../src/features/chat/api";
import {
  changePassword,
  deleteAccount,
  updateLanguage,
} from "../../src/features/profile/api";
import { ProfileScreen } from "../../src/features/profile/ProfileScreen";
import i18n from "../../src/i18n";

jest.mock("../../src/features/profile/api", () => ({
  updateLanguage: jest.fn(),
  changePassword: jest.fn(),
  deleteAccount: jest.fn(),
}));
jest.mock("../../src/features/chat/api", () => ({ getUsage: jest.fn() }));
const mockPush = jest.fn();
jest.mock("expo-router", () => ({ useRouter: () => ({ push: mockPush }) }));

const usage = getUsage as jest.MockedFunction<typeof getUsage>;
const language = updateLanguage as jest.MockedFunction<typeof updateLanguage>;
const change = changePassword as jest.MockedFunction<typeof changePassword>;
const remove = deleteAccount as jest.MockedFunction<typeof deleteAccount>;

function user(overrides: Partial<User> = {}): User {
  return {
    id: "u1",
    email: "learner@example.com",
    email_verified: true,
    locale: "vi",
    role: "user",
    created_at: "2026-11-13T00:00:00Z",
    ...overrides,
  };
}

function renderScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ProfileScreen />
    </QueryClientProvider>,
  );
}

const RESETS = "2026-11-13T17:00:00Z";

beforeEach(async () => {
  jest.clearAllMocks();
  await i18n.changeLanguage("vi");
  useAuthStore.setState({ status: "signedIn", user: user() });
  usage.mockResolvedValue({
    daily_limit: 30,
    used_today: 4,
    remaining: 26,
    resets_at: RESETS,
    card_suggestions: {
      daily_limit: 10,
      used_today: 1,
      remaining: 9,
      resets_at: RESETS,
    },
    quizzes: { daily_limit: 5, used_today: 2, remaining: 3, resets_at: RESETS },
  });
});

it("shows the account and today's AI allowance", async () => {
  renderScreen();
  expect(screen.getByTestId("profile-email").props.children).toBe(
    "learner@example.com",
  );
  expect(await screen.findByText("Còn 26/30 câu hỏi hôm nay")).toBeTruthy();
  expect(
    screen.getByText("Còn 9/10 lượt tạo thẻ bằng AI hôm nay"),
  ).toBeTruthy();
});

it("switches the interface language and saves it on the account", async () => {
  language.mockResolvedValue(user({ locale: "en" }));
  renderScreen();

  fireEvent.press(screen.getByTestId("profile-language-en"));

  await waitFor(() => expect(language).toHaveBeenCalledWith("en"));
  await waitFor(() => expect(i18n.language).toBe("en"));
  expect(await screen.findByText("Interface language")).toBeTruthy();
});

it("links unverified users to verification", () => {
  useAuthStore.setState({
    status: "signedIn",
    user: user({ email_verified: false }),
  });
  renderScreen();
  fireEvent.press(screen.getByTestId("profile-verify"));
  expect(mockPush).toHaveBeenCalledWith("/spaces/verify-email");
});

it("changes the password and explains a wrong current password", async () => {
  change
    .mockRejectedValueOnce(new ApiError("INVALID_PASSWORD", "x", 403))
    .mockResolvedValueOnce(user());
  renderScreen();

  fireEvent.press(screen.getByTestId("profile-change-password"));
  fireEvent.changeText(screen.getByTestId("change-current"), "wrong");
  fireEvent.changeText(
    screen.getByTestId("change-new"),
    "a brand new passphrase",
  );
  fireEvent.changeText(
    screen.getByTestId("change-confirm"),
    "a brand new passphrase",
  );
  fireEvent.press(screen.getByTestId("change-save"));
  expect(await screen.findByText("Mật khẩu hiện tại không đúng.")).toBeTruthy();

  fireEvent.changeText(
    screen.getByTestId("change-current"),
    "a long enough passphrase",
  );
  fireEvent.press(screen.getByTestId("change-save"));
  await waitFor(() =>
    expect(change).toHaveBeenLastCalledWith(
      "a long enough passphrase",
      "a brand new passphrase",
    ),
  );
  await waitFor(() =>
    expect(screen.queryByTestId("change-password-dialog")).toBeNull(),
  );
});

it("deletes the account with the password and signs out", async () => {
  remove.mockResolvedValue(undefined);
  renderScreen();

  fireEvent.press(screen.getByTestId("profile-delete"));
  expect(screen.getByText(/không khôi phục được/)).toBeTruthy();
  fireEvent.changeText(
    screen.getByTestId("delete-confirmation"),
    "a long enough passphrase",
  );
  fireEvent.press(screen.getByTestId("delete-account-confirm"));

  await waitFor(() => expect(useAuthStore.getState().status).toBe("signedOut"));
  expect(remove).toHaveBeenCalledWith({ password: "a long enough passphrase" });
});

it("asks Google-only accounts to retype their email", async () => {
  remove
    .mockRejectedValueOnce(new ApiError("NO_PASSWORD", "x", 409))
    .mockResolvedValueOnce(undefined);
  renderScreen();

  fireEvent.press(screen.getByTestId("profile-delete"));
  fireEvent.changeText(screen.getByTestId("delete-confirmation"), "anything");
  fireEvent.press(screen.getByTestId("delete-account-confirm"));
  expect(await screen.findByText(/hãy nhập lại email/)).toBeTruthy();

  fireEvent.changeText(
    screen.getByTestId("delete-confirmation"),
    "learner@example.com",
  );
  fireEvent.press(screen.getByTestId("delete-account-confirm"));
  await waitFor(() =>
    expect(remove).toHaveBeenLastCalledWith({
      confirmEmail: "learner@example.com",
    }),
  );
});
