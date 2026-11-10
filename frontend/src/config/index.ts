import Constants from "expo-constants";

interface AppConfig {
  apiUrl: string;
  appEnv: "development" | "staging" | "production";
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
};

export const isDev = config.appEnv === "development";
export const isProduction = config.appEnv === "production";
