import { useQuery } from "@tanstack/react-query";

import { getSystemStatus } from "./api";

export const systemStatusQueryKey = ["system", "status"] as const;

const REFRESH_INTERVAL_MS = 15_000;

/** Backend and dependency status, refreshed every 15 seconds. */
export function useSystemStatus() {
  return useQuery({
    queryKey: systemStatusQueryKey,
    queryFn: ({ signal }) => getSystemStatus(signal),
    refetchInterval: REFRESH_INTERVAL_MS,
    staleTime: 0,
    // The API client already retries network errors; fail fast here.
    retry: false,
  });
}
