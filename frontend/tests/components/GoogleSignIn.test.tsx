import { render, screen, waitFor } from "@testing-library/react-native";

import { ApiError } from "../../src/api/errors";
import { signInWithGoogle } from "../../src/features/auth/api";
import { GoogleSignInButton } from "../../src/features/auth/GoogleSignInButton";
import { authErrorMessage } from "../../src/features/auth/errorMessage";
import { googleClientIdFor } from "../../src/features/auth/googleClient";
import i18n from "../../src/i18n";

const IDS = {
  webClientId: "web-id",
  androidClientId: "",
  iosClientId: "ios-id",
};
let mockGoogleResponse: unknown = null;

jest.mock("../../src/config", () => ({
  config: {
    apiUrl: "http://test",
    appEnv: "development",
    google: {
      webClientId: "web-id",
      androidClientId: "android-id",
      iosClientId: "ios-id",
    },
  },
}));
jest.mock("expo-web-browser", () => ({ maybeCompleteAuthSession: jest.fn() }));
jest.mock("expo-auth-session/providers/google", () => ({
  useIdTokenAuthRequest: () => [{}, mockGoogleResponse, jest.fn()],
}));
jest.mock("../../src/features/auth/api", () => ({
  signInWithGoogle: jest.fn(),
}));

beforeEach(async () => {
  jest.clearAllMocks();
  mockGoogleResponse = null;
  await i18n.changeLanguage("vi");
});

it("picks the client ID of the platform, or none", () => {
  expect(googleClientIdFor("web", IDS)).toBe("web-id");
  expect(googleClientIdFor("ios", IDS)).toBe("ios-id");
  expect(googleClientIdFor("android", IDS)).toBeNull();
});

it("sends the Google ID token to the backend and signs in", async () => {
  const user = { id: "u1" };
  (signInWithGoogle as jest.Mock).mockResolvedValue(user);
  mockGoogleResponse = { type: "success", params: { id_token: "google-jwt" } };
  const onSignedIn = jest.fn();

  render(<GoogleSignInButton onSignedIn={onSignedIn} onError={jest.fn()} />);

  expect(screen.getByTestId("auth-google")).toBeTruthy();
  await waitFor(() => expect(onSignedIn).toHaveBeenCalledWith(user));
  expect(signInWithGoogle).toHaveBeenCalledWith("google-jwt", "vi");
});

it("explains why Google could not sign in", () => {
  const t = i18n.t.bind(i18n);
  expect(
    authErrorMessage(new ApiError("GOOGLE_LINK_REQUIRED", "x", 409), t),
  ).toMatch(/Đăng nhập bằng mật khẩu trước/);
  expect(
    authErrorMessage(new ApiError("GOOGLE_NOT_CONFIGURED", "x", 503), t),
  ).toMatch(/chưa được thiết lập/);
});
