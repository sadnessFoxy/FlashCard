/**
 * Gọi API hệ thống. Kiểu dữ liệu lấy từ src/api/generated (sinh từ contract/openapi.yaml).
 */
import { api } from "../../api/client";
import type { components } from "../../api/generated/schema";

export type SystemStatus = components["schemas"]["SystemStatusResponse"];
export type DependencyCheck = components["schemas"]["DependencyCheck"];
export type DatabaseCheck = components["schemas"]["DatabaseCheck"];
export type CheckErrorCode = NonNullable<DependencyCheck["error_code"]>;

export const SYSTEM_STATUS_PATH = "/v1/system/status";

export function getSystemStatus(signal?: AbortSignal): Promise<SystemStatus> {
  return api.get<SystemStatus>(SYSTEM_STATUS_PATH, {
    skipAuth: true,
    ...(signal ? { signal } : {}),
  });
}
