import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createSpace,
  deleteSpace,
  getSpace,
  listSpaces,
  renameSpace,
  type Space,
} from "./api";

export const spaceKeys = {
  all: ["spaces"] as const,
  detail: (id: string) => ["spaces", id] as const,
};

export function useSpaces() {
  return useQuery({
    queryKey: spaceKeys.all,
    queryFn: ({ signal }) => listSpaces(signal),
  });
}

export function useSpace(id: string) {
  return useQuery({
    queryKey: spaceKeys.detail(id),
    queryFn: ({ signal }) => getSpace(id, signal),
    // 404 means gone or not ours: retrying will not help.
    retry: false,
  });
}

/** Keep the list newest-first like the server, without refetching. */
function upsert(list: Space[] | undefined, space: Space): Space[] {
  return [space, ...(list ?? []).filter((s) => s.id !== space.id)];
}

export function useCreateSpace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => createSpace(name),
    onSuccess: (space) => {
      qc.setQueryData<Space[]>(spaceKeys.all, (list) => upsert(list, space));
      qc.setQueryData(spaceKeys.detail(space.id), space);
    },
  });
}

export function useRenameSpace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      renameSpace(id, name),
    onSuccess: (space) => {
      qc.setQueryData<Space[]>(spaceKeys.all, (list) => upsert(list, space));
      qc.setQueryData(spaceKeys.detail(space.id), space);
    },
  });
}

export function useDeleteSpace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteSpace(id),
    onSuccess: (_void, id) => {
      qc.setQueryData<Space[]>(spaceKeys.all, (list) =>
        (list ?? []).filter((s) => s.id !== id),
      );
      qc.removeQueries({ queryKey: spaceKeys.detail(id) });
    },
  });
}
