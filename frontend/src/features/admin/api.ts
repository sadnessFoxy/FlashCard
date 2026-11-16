import { api } from "../../api/client";
import type { components } from "../../api/generated/schema";

type Schemas = components["schemas"];
export type AdminOverview = Schemas["AdminOverview"];
export type AdminUser = Schemas["AdminUser"];
export type AdminUserList = Schemas["AdminUserList"];
export type AdminDocument = Schemas["AdminDocument"];
export type AdminSettings = Schemas["AdminSettings"];
export type AdminAuditEntry = Schemas["AdminAuditEntry"];

const userPath = (id: string) => `/v1/admin/users/${encodeURIComponent(id)}`;

export const getOverview = () => api.get<AdminOverview>("/v1/admin/overview");

export function listUsers(query: string) {
  const params = new URLSearchParams({ limit: "100" });
  if (query.trim()) params.set("q", query.trim());
  return api.get<AdminUserList>(`/v1/admin/users?${params.toString()}`);
}

export const getUser = (id: string) => api.get<AdminUser>(userPath(id));

export const blockUser = (id: string, reason: string) =>
  api.post<AdminUser>(`${userPath(id)}/block`, { reason });

export const unblockUser = (id: string) =>
  api.post<AdminUser>(`${userPath(id)}/unblock`);

export const signOutUser = (id: string) =>
  api.post<void>(`${userPath(id)}/sign-out`);

export const setUserQuota = (
  id: string,
  dailyLimit: number | null,
  expiresAt: string | null,
) =>
  api.put<AdminUser>(`${userPath(id)}/quota`, {
    daily_limit: dailyLimit,
    expires_at: expiresAt,
  });

export const deleteUser = (id: string, reason: string) =>
  api.post<void>(`${userPath(id)}/deletion`, { reason });

export function listDocuments(status: string | null) {
  const params = new URLSearchParams({ limit: "100" });
  if (status) params.set("status", status);
  return api.get<{ items: AdminDocument[] }>(
    `/v1/admin/documents?${params.toString()}`,
  );
}

export const retryDocument = (id: string) =>
  api.post<AdminDocument>(
    `/v1/admin/documents/${encodeURIComponent(id)}/retry`,
  );

export const getSettings = () => api.get<AdminSettings>("/v1/admin/settings");

export const updateSettings = (values: Record<string, unknown>) =>
  api.patch<AdminSettings>("/v1/admin/settings", { values });

export function listAudit(action: string | null) {
  const params = new URLSearchParams({ limit: "200" });
  if (action) params.set("action", action);
  return api.get<{ items: AdminAuditEntry[] }>(
    `/v1/admin/audit?${params.toString()}`,
  );
}
