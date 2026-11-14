import { api, storeSessionTokens } from "../../api/client";
import type { components } from "../../api/generated/schema";
import { clearTokens } from "../../storage/session";
import type { Locale, User } from "../auth/api";

type AuthSession = components["schemas"]["AuthSession"];

export function updateLanguage(locale: Locale): Promise<User> {
  return api.patch<User>("/v1/me", { locale });
}

/** Other sessions are signed out; this device keeps going with the new tokens. */
export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<User> {
  const session = await api.post<AuthSession>("/v1/auth/password/change", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  await storeSessionTokens(session);
  return session.user;
}

/** Password accounts send the password; Google-only accounts retype the email. */
export async function deleteAccount(confirmation: {
  password?: string;
  confirmEmail?: string;
}): Promise<void> {
  await api.post<void>("/v1/me/deletion", {
    password: confirmation.password ?? null,
    confirm_email: confirmation.confirmEmail ?? null,
  });
  await clearTokens();
}
