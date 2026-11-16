import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  blockUser,
  deleteUser,
  getOverview,
  getSettings,
  getUser,
  listAudit,
  listDocuments,
  listUsers,
  retryDocument,
  setUserQuota,
  signOutUser,
  unblockUser,
  updateSettings,
} from "./api";

const ADMIN = ["admin"] as const;

export const useOverview = () =>
  useQuery({ queryKey: [...ADMIN, "overview"], queryFn: getOverview });

export const useAdminUsers = (query: string) =>
  useQuery({
    queryKey: [...ADMIN, "users", query],
    queryFn: () => listUsers(query),
  });

export const useAdminUser = (id: string) =>
  useQuery({
    queryKey: [...ADMIN, "user", id],
    queryFn: () => getUser(id),
    retry: false,
  });

export const useAdminDocuments = (status: string | null) =>
  useQuery({
    queryKey: [...ADMIN, "documents", status],
    queryFn: () => listDocuments(status),
  });

export const useAdminSettings = () =>
  useQuery({ queryKey: [...ADMIN, "settings"], queryFn: getSettings });

export const useAudit = (action: string | null) =>
  useQuery({
    queryKey: [...ADMIN, "audit", action],
    queryFn: () => listAudit(action),
  });

/** Every admin change refreshes all admin data (counts and the audit log move together). */
function useAdminMutation<TArgs, TResult>(
  fn: (args: TArgs) => Promise<TResult>,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ADMIN }),
  });
}

export const useBlockUser = () =>
  useAdminMutation(({ id, reason }: { id: string; reason: string }) =>
    blockUser(id, reason),
  );
export const useUnblockUser = () =>
  useAdminMutation((id: string) => unblockUser(id));
export const useSignOutUser = () =>
  useAdminMutation((id: string) => signOutUser(id));
export const useSetUserQuota = () =>
  useAdminMutation(
    ({
      id,
      dailyLimit,
      expiresAt,
    }: {
      id: string;
      dailyLimit: number | null;
      expiresAt: string | null;
    }) => setUserQuota(id, dailyLimit, expiresAt),
  );
export const useDeleteUser = () =>
  useAdminMutation(({ id, reason }: { id: string; reason: string }) =>
    deleteUser(id, reason),
  );
export const useRetryDocument = () =>
  useAdminMutation((id: string) => retryDocument(id));
export const useUpdateSettings = () =>
  useAdminMutation((values: Record<string, unknown>) => updateSettings(values));
