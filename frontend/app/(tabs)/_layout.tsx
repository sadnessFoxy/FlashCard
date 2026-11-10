import { Redirect, Tabs } from "expo-router";
import { useTranslation } from "react-i18next";

import { SplashScreen } from "../../src/components/feedback/SplashScreen";
import { useAuthStore } from "../../src/features/auth/useAuthStore";
import { colors } from "../../src/theme/tokens";

// Main navigation per docs/SCREENS.md: Spaces, Cards (F9), Profile.
export default function TabsLayout() {
  const { t } = useTranslation();
  const status = useAuthStore((s) => s.status);

  if (status === "unknown") return <SplashScreen />;
  if (status !== "signedIn") return <Redirect href="/" />;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
      }}
    >
      <Tabs.Screen name="spaces" options={{ title: t("tabs.spaces") }} />
      <Tabs.Screen name="profile" options={{ title: t("tabs.profile") }} />
    </Tabs>
  );
}
