import { ExpoConfig, ConfigContext } from "expo/config";

const APP_ENV = process.env.APP_ENV ?? "development";

const envConfig = {
  development: {
    name: "FlashCard (Dev)",
    slug: "flashcard-dev",
    apiUrl: "http://localhost:8000/v1",
    bundleIdentifier: "com.example.flashcard.dev",
    androidPackage: "com.example.flashcard.dev",
  },
  staging: {
    name: "FlashCard (Staging)",
    slug: "flashcard-staging",
    apiUrl: "https://api-staging.example.com/v1",
    bundleIdentifier: "com.example.flashcard.staging",
    androidPackage: "com.example.flashcard.staging",
  },
  production: {
    name: "FlashCard",
    slug: "flashcard",
    apiUrl: "https://api.example.com/v1",
    bundleIdentifier: "com.example.flashcard",
    androidPackage: "com.example.flashcard",
  },
} as const;

const env = envConfig[APP_ENV as keyof typeof envConfig] ?? envConfig.development;

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: env.name,
  slug: env.slug,
  version: "1.0.0",
  orientation: "portrait",
  icon: "./assets/icon.png",
  userInterfaceStyle: "automatic",
  splash: {
    image: "./assets/splash.png",
    resizeMode: "contain",
    backgroundColor: "#ffffff",
  },
  assetBundlePatterns: ["**/*"],
  ios: {
    supportsTablet: true,
    bundleIdentifier: env.bundleIdentifier,
    // NOTE: Chỉ bản thử nghiệm, không submit lên App Store
  },
  android: {
    adaptiveIcon: {
      foregroundImage: "./assets/adaptive-icon.png",
      backgroundColor: "#ffffff",
    },
    package: env.androidPackage,
    // NOTE: Chỉ bản thử nghiệm, không submit lên Google Play
  },
  web: {
    favicon: "./assets/favicon.png",
    bundler: "metro",
  },
  plugins: [
    "expo-router",
    "expo-secure-store",
    [
      "expo-dev-client",
      {
        addGeneratedScheme: false,
      },
    ],
  ],
  scheme: "flashcard",
  extra: {
    apiUrl: env.apiUrl,
    appEnv: APP_ENV,
    eas: {
      projectId: "your-eas-project-id",
    },
  },
  experiments: {
    typedRoutes: true,
  },
});
