import { api } from "../../api/client";
import type { components } from "../../api/generated/schema";

export type Space = components["schemas"]["Space"];
type SpaceList = components["schemas"]["SpaceList"];

export async function listSpaces(signal?: AbortSignal): Promise<Space[]> {
  const body = await api.get<SpaceList>("/v1/spaces", signal ? { signal } : {});
  return body.items;
}

export function getSpace(id: string, signal?: AbortSignal): Promise<Space> {
  return api.get<Space>(
    `/v1/spaces/${encodeURIComponent(id)}`,
    signal ? { signal } : {},
  );
}

export function createSpace(name: string): Promise<Space> {
  return api.post<Space>("/v1/spaces", { name });
}

export function renameSpace(id: string, name: string): Promise<Space> {
  return api.patch<Space>(`/v1/spaces/${encodeURIComponent(id)}`, { name });
}

export function deleteSpace(id: string): Promise<void> {
  return api.delete<void>(`/v1/spaces/${encodeURIComponent(id)}`);
}
