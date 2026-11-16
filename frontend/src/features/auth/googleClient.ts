import { Platform } from "react-native";

import { config, type GoogleClientIds } from "../../config";

/** The OAuth client ID this platform needs; null hides the Google button. */
export function googleClientIdFor(
  os: string = Platform.OS,
  ids: GoogleClientIds = config.google,
): string | null {
  const id =
    os === "web"
      ? ids.webClientId
      : os === "android"
        ? ids.androidClientId
        : os === "ios"
          ? ids.iosClientId
          : "";
  return id || null;
}
