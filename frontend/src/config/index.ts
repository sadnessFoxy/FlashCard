import Constants from "expo-constants";

export interface GoogleClientIds {
  webClientId: string;
  androidClientId: string;
  iosClientId: string;
}

interface AppConfig {
  apiUrl: string;
  appEnv: "development" | "staging" | "production";
  google: GoogleClientIds;
}

const extra = Constants.expoConfig?.extra as AppConfig | undefined;

if (!extra?.apiUrl) {
  throw new Error(
    "Missing apiUrl in app config. Check app.config.ts and APP_ENV environment variable.",
  );
}

export const config: AppConfig = {
  apiUrl: extra.apiUrl,
  appEnv: extra.appEnv ?? "development",
  google: extra.google ?? {
    webClientId: "",
    androidClientId: "",
    iosClientId: "",
  },
};

export const isDev = config.appEnv === "development";
export const isProduction = config.appEnv === "production";
