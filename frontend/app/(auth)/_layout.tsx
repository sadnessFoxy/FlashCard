import { Redirect, Stack } from "expo-router";

import { useAuthStore } from "../../src/features/auth/useAuthStore";

export default function AuthLayout() {
  const status = useAuthStore((s) => s.status);
  if (status === "signedIn") return <Redirect href="/spaces" />;
  // forgot-password arrives in F4
  return <Stack screenOptions={{ headerShown: false, animation: "fade" }} />;
}
