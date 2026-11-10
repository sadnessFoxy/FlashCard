/**
 * Re-export session storage.
 * Metro picks the platform file automatically:
 *   - session.native.ts on iOS and Android
 *   - session.web.ts cho web
 * This file only serves tsc and Jest; import "storage/session" and let Metro resolve.
 */
export * from "./session.native";
