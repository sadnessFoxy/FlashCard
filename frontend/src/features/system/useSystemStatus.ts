import { useQuery } from "@tanstack/react-query";

import { getSystemStatus } from "./api";

export const systemStatusQueryKey = ["system", "status"] as const;

const REFRESH_INTERVAL_MS = 15_000;

/** Trạng thái backend và các phụ thuộc, tự làm mới mỗi 15 giây. */
export function useSystemStatus() {
  return useQuery({
    queryKey: systemStatusQueryKey,
    queryFn: ({ signal }) => getSystemStatus(signal),
    refetchInterval: REFRESH_INTERVAL_MS,
    staleTime: 0,
    // API client đã tự thử lại khi lỗi mạng; không thử thêm để báo lỗi nhanh.
    retry: false,
  });
}
