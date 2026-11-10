import { Redirect } from "expo-router";

import { SplashScreen } from "../src/components/feedback/SplashScreen";
import { useAuthStore } from "../src/features/auth/useAuthStore";

export default function Index() {
  const status = useAuthStore((s) => s.status);
  const bootstrap = useAuthStore((s) => s.bootstrap);

  switch (status) {
    case "signedIn":
      return <Redirect href="/spaces" />;
    case "signedOut":
      return <Redirect href="/login" />;
    case "unreachable":
      return <SplashScreen onRetry={() => void bootstrap()} />;
    default:
      return <SplashScreen />;
  }
}
