import { create } from "zustand";

import { ApiError } from "../../api/errors";
import { getMe, logout as logoutRequest, type User } from "./api";

/**
 * - unknown: checking the stored session on startup
 * - unreachable: could not ask the backend (network); not the same as signed out
 */
export type AuthStatus = "unknown" | "unreachable" | "signedIn" | "signedOut";

interface AuthState {
  status: AuthStatus;
  user: User | null;
  bootstrap: () => Promise<void>;
  signedIn: (user: User) => void;
  /** The server returned a newer copy of the user (e.g. after verifying the email). */
  userUpdated: (user: User) => void;
  /** Local-only sign-out, e.g. when refresh failed. */
  sessionEnded: () => void;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  status: "unknown",
  user: null,

  bootstrap: async () => {
    set({ status: "unknown" });
    try {
      set({ status: "signedIn", user: await getMe() });
    } catch (error) {
      const offline = error instanceof ApiError && error.isNetworkError;
      set({ status: offline ? "unreachable" : "signedOut", user: null });
    }
  },

  signedIn: (user) => set({ status: "signedIn", user }),

  userUpdated: (user) => set({ user }),

  sessionEnded: () => set({ status: "signedOut", user: null }),

  logout: async () => {
    await logoutRequest();
    set({ status: "signedOut", user: null });
  },
}));
