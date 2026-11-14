import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createQuiz,
  deleteQuiz,
  getQuiz,
  listQuizzes,
  submitAttempt,
  type CreateQuizRequest,
} from "./api";

export const quizKeys = {
  all: ["quizzes"] as const,
  inSpace: (spaceId: string) => ["quizzes", "space", spaceId] as const,
  detail: (id: string) => ["quizzes", "detail", id] as const,
};

export function useQuizzes(spaceId: string) {
  return useQuery({
    queryKey: quizKeys.inSpace(spaceId),
    queryFn: ({ signal }) => listQuizzes(spaceId, signal),
  });
}

export function useQuiz(id: string) {
  return useQuery({
    queryKey: quizKeys.detail(id),
    queryFn: ({ signal }) => getQuiz(id, signal),
    retry: false,
  });
}

export function useCreateQuiz() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateQuizRequest) => createQuiz(request),
    onSuccess: (quiz) => {
      qc.setQueryData(quizKeys.detail(quiz.id), quiz);
      void qc.invalidateQueries({ queryKey: quizKeys.all });
      void qc.invalidateQueries({ queryKey: ["usage"] });
    },
  });
}

export function useSubmitAttempt(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (answers: { question_id: string; choice: number | null }[]) =>
      submitAttempt(id, answers),
    onSuccess: () => void qc.invalidateQueries({ queryKey: quizKeys.all }),
  });
}

export function useDeleteQuiz() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteQuiz(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: quizKeys.all }),
  });
}
