import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { useEffect } from "react";

import { onSessionExpired } from "../src/api/client";
import { useAuthStore } from "../src/features/auth/useAuthStore";
import "../src/i18n";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, staleTime: 1000 * 60 * 5 },
    mutations: { retry: 0 },
  },
});

export default function RootLayout() {
  const bootstrap = useAuthStore((s) => s.bootstrap);
  const sessionEnded = useAuthStore((s) => s.sessionEnded);

  useEffect(() => {
    onSessionExpired(() => {
      queryClient.clear(); // never show the previous user's cached data
      sessionEnded();
    });
    void bootstrap();
    return () => onSessionExpired(null);
  }, [bootstrap, sessionEnded]);

  return (
    <QueryClientProvider client={queryClient}>
      <Stack screenOptions={{ headerShown: false }} />
    </QueryClientProvider>
  );
}
