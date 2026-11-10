import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { ApiError, NetworkError } from "../../src/api/errors";
import { login, register, type User } from "../../src/features/auth/api";
import { LoginScreen } from "../../src/features/auth/LoginScreen";
import { useAuthStore } from "../../src/features/auth/useAuthStore";
import i18n from "../../src/i18n";

jest.mock("../../src/features/auth/api", () => ({
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
}));

const mockedLogin = login as jest.MockedFunction<typeof login>;
const mockedRegister = register as jest.MockedFunction<typeof register>;

const USER: User = {
  id: "7f0c6a9e-0000-4000-8000-000000000001",
  email: "an@example.com",
  email_verified: false,
  locale: "vi",
  role: "user",
  created_at: "2026-11-10T00:00:00Z",
};

function fill(email: string, password: string, confirm?: string) {
  fireEvent.changeText(screen.getByTestId("auth-email"), email);
  fireEvent.changeText(screen.getByTestId("auth-password"), password);
  if (confirm !== undefined)
    fireEvent.changeText(screen.getByTestId("auth-confirm"), confirm);
}

const submit = () => fireEvent.press(screen.getByTestId("auth-submit"));

beforeEach(async () => {
  jest.clearAllMocks();
  useAuthStore.setState({ status: "signedOut", user: null });
  await i18n.changeLanguage("vi");
});

it("signs in and updates the session", async () => {
  mockedLogin.mockResolvedValue(USER);
  render(<LoginScreen />);

  fill(" an@example.com ", "correct horse battery");
  submit();

  await waitFor(() => expect(useAuthStore.getState().status).toBe("signedIn"));
  expect(mockedLogin).toHaveBeenCalledWith({
    email: "an@example.com",
    password: "correct horse battery",
  });
  expect(useAuthStore.getState().user).toEqual(USER);
});

it("validates fields before calling the API", () => {
  render(<LoginScreen />);

  fill("not-an-email", "");
  submit();

  expect(screen.getByText("Email không đúng định dạng")).toBeTruthy();
  expect(screen.getByText("Hãy nhập mật khẩu")).toBeTruthy();
  expect(mockedLogin).not.toHaveBeenCalled();
});

it("shows one generic message for wrong credentials", async () => {
  mockedLogin.mockRejectedValue(new ApiError("INVALID_CREDENTIALS", "x", 401));
  render(<LoginScreen />);

  fill("an@example.com", "wrong password");
  submit();

  expect(
    await screen.findByText("Email hoặc mật khẩu không đúng"),
  ).toBeTruthy();
  expect(useAuthStore.getState().status).toBe("signedOut");
});

it("tells how long to wait when rate limited", async () => {
  mockedLogin.mockRejectedValue(
    new ApiError("TOO_MANY_ATTEMPTS", "x", 429, { retryAfterSeconds: 610 }),
  );
  render(<LoginScreen />);

  fill("an@example.com", "whatever pass");
  submit();

  expect(await screen.findByText(/thử lại sau 11 phút/)).toBeTruthy();
});

it("reports a blocked account", async () => {
  mockedLogin.mockRejectedValue(new ApiError("ACCOUNT_BLOCKED", "x", 403));
  render(<LoginScreen />);

  fill("an@example.com", "right password");
  submit();

  expect(await screen.findByText(/đã bị khóa/)).toBeTruthy();
});

it("shows a network error without leaking technical text", async () => {
  mockedLogin.mockRejectedValue(new NetworkError("TypeError: Failed to fetch"));
  render(<LoginScreen />);

  fill("an@example.com", "right password");
  submit();

  expect(await screen.findByText("Lỗi kết nối mạng")).toBeTruthy();
  expect(screen.queryByText(/Failed to fetch/)).toBeNull();
});

describe("sign up", () => {
  beforeEach(() => {
    render(<LoginScreen />);
    fireEvent.press(screen.getByTestId("auth-tab-register"));
  });

  it("checks length and confirmation locally", () => {
    fill("an@example.com", "short", "different");
    submit();

    expect(screen.getByText("Mật khẩu cần ít nhất 8 ký tự")).toBeTruthy();
    expect(screen.getByText("Hai mật khẩu không khớp")).toBeTruthy();
    expect(mockedRegister).not.toHaveBeenCalled();
  });

  it("registers with the current UI language", async () => {
    mockedRegister.mockResolvedValue(USER);

    fill("an@example.com", "correct horse battery", "correct horse battery");
    submit();

    await waitFor(() =>
      expect(useAuthStore.getState().status).toBe("signedIn"),
    );
    expect(mockedRegister).toHaveBeenCalledWith(
      { email: "an@example.com", password: "correct horse battery" },
      "vi",
    );
  });

  it("explains a weak password reported by the server", async () => {
    mockedRegister.mockRejectedValue(
      new ApiError("WEAK_PASSWORD", "x", 422, { reason: "too_common" }),
    );

    fill("an@example.com", "password123", "password123");
    submit();

    expect(await screen.findByText(/quá phổ biến/)).toBeTruthy();
  });

  it("uses the generic message for an existing email", async () => {
    mockedRegister.mockRejectedValue(
      new ApiError("EMAIL_UNAVAILABLE", "x", 409),
    );

    fill("an@example.com", "correct horse battery", "correct horse battery");
    submit();

    expect(
      await screen.findByText(/Không thể đăng ký bằng email này/),
    ).toBeTruthy();
  });
});

it("renders in English", async () => {
  await i18n.changeLanguage("en");
  render(<LoginScreen />);

  fill("bad", "");
  submit();

  expect(screen.getByText("Enter a valid email address")).toBeTruthy();
  expect(screen.getAllByText("Sign in").length).toBeGreaterThan(0);
});
