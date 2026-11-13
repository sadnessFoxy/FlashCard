import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { ApiError } from "../../src/api/errors";
import {
  confirmEmailVerification,
  confirmPasswordReset,
  requestPasswordReset,
  sendEmailVerification,
  type User,
} from "../../src/features/auth/api";
import { ForgotPasswordScreen } from "../../src/features/auth/ForgotPasswordScreen";
import { useAuthStore } from "../../src/features/auth/useAuthStore";
import { VerifyEmailBanner } from "../../src/features/auth/VerifyEmailBanner";
import { VerifyEmailScreen } from "../../src/features/auth/VerifyEmailScreen";
import i18n from "../../src/i18n";

jest.mock("../../src/features/auth/api", () => ({
  ...jest.requireActual("../../src/features/auth/api"),
  sendEmailVerification: jest.fn(),
  confirmEmailVerification: jest.fn(),
  requestPasswordReset: jest.fn(),
  confirmPasswordReset: jest.fn(),
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

const requestReset = requestPasswordReset as jest.MockedFunction<
  typeof requestPasswordReset
>;
const confirmReset = confirmPasswordReset as jest.MockedFunction<
  typeof confirmPasswordReset
>;
const resend = sendEmailVerification as jest.MockedFunction<
  typeof sendEmailVerification
>;
const verify = confirmEmailVerification as jest.MockedFunction<
  typeof confirmEmailVerification
>;

function user(verified: boolean): User {
  return {
    id: "u1",
    email: "learner@example.com",
    email_verified: verified,
    locale: "vi",
    role: "user",
    created_at: "2026-11-13T00:00:00Z",
  };
}

beforeEach(async () => {
  jest.clearAllMocks();
  await i18n.changeLanguage("vi");
});

describe("ForgotPasswordScreen", () => {
  it("asks for a code, then sets the new password", async () => {
    requestReset.mockResolvedValue(undefined);
    confirmReset.mockResolvedValue(undefined);
    render(<ForgotPasswordScreen />);

    fireEvent.changeText(
      screen.getByTestId("forgot-email"),
      " learner@example.com ",
    );
    fireEvent.press(screen.getByTestId("forgot-send"));
    expect(await screen.findByTestId("forgot-sent")).toBeTruthy();
    expect(requestReset).toHaveBeenCalledWith("learner@example.com");

    fireEvent.changeText(screen.getByTestId("forgot-code"), "123456");
    fireEvent.changeText(
      screen.getByTestId("forgot-password"),
      "a brand new passphrase",
    );
    fireEvent.changeText(
      screen.getByTestId("forgot-confirm"),
      "a brand new passphrase",
    );
    fireEvent.press(screen.getByTestId("forgot-submit"));

    expect(await screen.findByTestId("forgot-done")).toBeTruthy();
    expect(confirmReset).toHaveBeenCalledWith(
      "learner@example.com",
      "123456",
      "a brand new passphrase",
    );
  });

  it("validates the email and explains a wrong code", async () => {
    requestReset.mockResolvedValue(undefined);
    confirmReset.mockRejectedValue(new ApiError("INVALID_CODE", "x", 400));
    render(<ForgotPasswordScreen />);

    fireEvent.changeText(screen.getByTestId("forgot-email"), "not-an-email");
    fireEvent.press(screen.getByTestId("forgot-send"));
    expect(await screen.findByText("Email không đúng định dạng")).toBeTruthy();
    expect(requestReset).not.toHaveBeenCalled();

    fireEvent.changeText(
      screen.getByTestId("forgot-email"),
      "learner@example.com",
    );
    fireEvent.press(screen.getByTestId("forgot-send"));
    fireEvent.changeText(await screen.findByTestId("forgot-code"), "000000");
    fireEvent.changeText(
      screen.getByTestId("forgot-password"),
      "a brand new passphrase",
    );
    fireEvent.changeText(
      screen.getByTestId("forgot-confirm"),
      "a brand new passphrase",
    );
    fireEvent.press(screen.getByTestId("forgot-submit"));

    expect(
      await screen.findByText(/Mã không đúng hoặc đã hết hạn/),
    ).toBeTruthy();
  });
});

describe("VerifyEmailScreen", () => {
  it("verifies with the code and updates the user", async () => {
    useAuthStore.setState({ status: "signedIn", user: user(false) });
    verify.mockResolvedValue(user(true));
    render(<VerifyEmailScreen />);

    fireEvent.changeText(screen.getByTestId("verify-code"), "654321");
    fireEvent.press(screen.getByTestId("verify-submit"));

    expect(await screen.findByTestId("verify-done")).toBeTruthy();
    expect(verify).toHaveBeenCalledWith("654321");
    expect(useAuthStore.getState().user?.email_verified).toBe(true);
  });

  it("resends and explains the rate limit", async () => {
    useAuthStore.setState({ status: "signedIn", user: user(false) });
    resend
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(
        new ApiError("TOO_MANY_ATTEMPTS", "x", 429, { retryAfterSeconds: 60 }),
      );
    render(<VerifyEmailScreen />);

    fireEvent.press(screen.getByTestId("verify-resend"));
    expect(await screen.findByText(/Đã gửi mã mới/)).toBeTruthy();
    fireEvent.press(screen.getByTestId("verify-resend"));
    expect(await screen.findByText(/thử lại sau 1 phút/)).toBeTruthy();
  });
});

describe("VerifyEmailBanner", () => {
  it("shows only for unverified users and opens the verify screen", async () => {
    useAuthStore.setState({ status: "signedIn", user: user(true) });
    const { unmount } = render(<VerifyEmailBanner />);
    expect(screen.queryByTestId("verify-banner")).toBeNull();
    unmount();

    useAuthStore.setState({ status: "signedIn", user: user(false) });
    render(<VerifyEmailBanner />);
    fireEvent.press(screen.getByTestId("verify-banner"));
    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith("/spaces/verify-email"),
    );
  });
});
