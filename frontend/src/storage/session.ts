/**
 * Re-export session storage.
 * Metro sẽ tự động chọn:
 *   - session.native.ts cho iOS và Android
 *   - session.web.ts cho web
 * File này không được import trực tiếp - dùng "session" và Metro tự resolve.
 */
export * from "./session.native";
