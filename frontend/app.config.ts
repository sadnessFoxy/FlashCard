import { ExpoConfig, ConfigContext } from "expo/config";

const APP_ENV = process.env.APP_ENV ?? "development";

const envConfig = {
  development: {
    name: "FlashCard (Dev)",
    slug: "flashcard-dev",
    apiUrl: "http://localhost:8000",
    bundleIdentifier: "com.example.flashcard.dev",
    androidPackage: "com.example.flashcard.dev",
  },
  staging: {
    name: "FlashCard (Staging)",
    slug: "flashcard-staging",
    apiUrl: "https://api-staging.example.com",
    bundleIdentifier: "com.example.flashcard.staging",
    androidPackage: "com.example.flashcard.staging",
  },
  production: {
    name: "FlashCard",
    slug: "flashcard",
    apiUrl: "https://api.example.com",
    bundleIdentifier: "com.example.flashcard",
    androidPackage: "com.example.flashcard",
  },
} as const;

const env = envConfig[APP_ENV as keyof typeof envConfig] ?? envConfig.development;

// Gốc API, KHÔNG kèm /v1 (đường dẫn trong contract đã có /v1).
// Thử trên điện thoại thật: đặt API_URL=http://<IP-máy-tính>:8000 vì "localhost" là chính điện thoại.
const apiUrl = process.env.API_URL ?? env.apiUrl;

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: env.name,
  slug: env.slug,
  version: "1.0.0",
  orientation: "portrait",
  userInterfaceStyle: "automatic",
  assetBundlePatterns: ["**/*"],
  ios: {
    supportsTablet: true,
    bundleIdentifier: env.bundleIdentifier,
    // NOTE: Chỉ bản thử nghiệm, không submit lên App Store
  },
  android: {
    package: env.androidPackage,
    // NOTE: Chỉ bản thử nghiệm, không submit lên Google Play
  },
  web: {
    bundler: "metro",
  },
  plugins: [
    "expo-router",
    "expo-secure-store",
    "expo-localization",
    [
      "expo-dev-client",
      {
        addGeneratedScheme: false,
      },
    ],
  ],
  scheme: "flashcard",
  extra: {
    apiUrl,
    appEnv: APP_ENV,
    eas: {
      projectId: "your-eas-project-id",
    },
  },
  experiments: {
    typedRoutes: true,
  },
});
