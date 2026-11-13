import { useQuery } from "@tanstack/react-query";

import { getConversation, getUsage, listConversations } from "./api";

export const chatKeys = {
  usage: ["usage", "me"] as const,
  list: (spaceId: string) => ["conversations", spaceId] as const,
  detail: (id: string) => ["conversation", id] as const,
};

export function useUsage() {
  return useQuery({
    queryKey: chatKeys.usage,
    queryFn: ({ signal }) => getUsage(signal),
  });
}

export function useConversations(spaceId: string) {
  return useQuery({
    queryKey: chatKeys.list(spaceId),
    queryFn: ({ signal }) => listConversations(spaceId, signal),
  });
}

export function useConversation(id: string | null) {
  return useQuery({
    queryKey: chatKeys.detail(id ?? "none"),
    queryFn: ({ signal }) => getConversation(id as string, signal),
    enabled: id !== null,
  });
}
