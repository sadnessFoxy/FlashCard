/**
 * Web session storage: httpOnly cookies set by the backend.
 * R12: tokens never go to localStorage or sessionStorage.
 *
 * The backend sets the cookies on sign-in; JavaScript can neither
 * read nor write them. Requests use credentials: "include".
 */

export async function saveAccessToken(_token: string): Promise<void> {
  // No-op: the backend sets the access cookie
}

export function getAccessToken(): Promise<string | null> {
  // httpOnly cookies are unreadable from JS by design;
  // the web client sends cookies instead of a Bearer header
  return Promise.resolve(null);
}

export async function saveRefreshToken(_token: string): Promise<void> {
  // No-op: the backend sets the refresh cookie
}

export function getRefreshToken(): Promise<string | null> {
  // Unreadable; the browser sends it to /v1/auth/refresh
  return Promise.resolve(null);
}

export async function clearTokens(): Promise<void> {
  // The backend clears cookies on /v1/auth/logout;
  // nothing to do client-side
}
