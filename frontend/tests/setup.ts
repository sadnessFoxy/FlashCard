/**
 * Global test setup. Screens import the API client, which needs an API URL from the
 * Expo config; give it one so tests only mock the feature APIs they exercise.
 */
jest.mock("expo-constants", () => {
  const actual = jest.requireActual("expo-constants");
  const constants = actual.default ?? actual;
  // Inherit everything else (expo-router reads other fields); override only expoConfig.
  const withApiUrl = Object.create(constants, {
    expoConfig: {
      value: {
        ...constants.expoConfig,
        extra: { apiUrl: "http://api.test", appEnv: "development" },
      },
    },
  });
  return { __esModule: true, ...actual, default: withApiUrl };
});

// In-memory AsyncStorage for the offline review queue.
jest.mock("@react-native-async-storage/async-storage", () =>
  jest.requireActual(
    "@react-native-async-storage/async-storage/jest/async-storage-mock",
  ),
);
