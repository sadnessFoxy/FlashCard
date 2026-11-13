import { CLIENT_PLATFORM, api, storeSessionTokens } from "../../api/client";
import type { components } from "../../api/generated/schema";
import { clearTokens, getRefreshToken } from "../../storage/session";

export type User = components["schemas"]["User"];
export type AuthSession = components["schemas"]["AuthSession"];
export type Locale = components["schemas"]["Locale"];

export interface Credentials {
  email: string;
  password: string;
}

async function startSession(session: AuthSession): Promise<User> {
  await storeSessionTokens(session);
  return session.user;
}

export async function register(
  credentials: Credentials,
  locale: Locale,
): Promise<User> {
  const session = await api.post<AuthSession>(
    "/v1/auth/register",
    { ...credentials, locale },
    { skipAuth: true },
  );
  return startSession(session);
}

export async function login(credentials: Credentials): Promise<User> {
  const session = await api.post<AuthSession>("/v1/auth/login", credentials, {
    skipAuth: true,
  });
  return startSession(session);
}

/** Revoke the session server-side when possible; always clear it locally. */
export async function logout(): Promise<void> {
  try {
    const refreshToken =
      CLIENT_PLATFORM === "web" ? null : await getRefreshToken();
    await api.post<void>(
      "/v1/auth/logout",
      refreshToken ? { refresh_token: refreshToken } : undefined,
      { skipAuth: true },
    );
  } catch {
    // Offline or server error: the token simply expires; local sign-out still happens.
  } finally {
    await clearTokens();
  }
}

export function getMe(): Promise<User> {
  return api.get<User>("/v1/me");
}

// ---------- email codes (docs/specs/f4-email-codes.md) ----------

export function sendEmailVerification(): Promise<void> {
  return api.post<void>("/v1/auth/email-verification");
}

export function confirmEmailVerification(code: string): Promise<User> {
  return api.post<User>("/v1/auth/email-verification/confirm", { code });
}

/** Always succeeds the same way, whether or not the email has an account. */
export function requestPasswordReset(email: string): Promise<void> {
  return api.post<void>(
    "/v1/auth/password-reset",
    { email },
    { skipAuth: true },
  );
}

export function confirmPasswordReset(
  email: string,
  code: string,
  newPassword: string,
): Promise<void> {
  return api.post<void>(
    "/v1/auth/password-reset/confirm",
    { email, code, new_password: newPassword },
    { skipAuth: true },
  );
}
