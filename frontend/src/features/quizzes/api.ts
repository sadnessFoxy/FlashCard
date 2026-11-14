import { api } from "../../api/client";
import type { components } from "../../api/generated/schema";

type Schemas = components["schemas"];
export type QuizSummary = Schemas["QuizSummary"];
export type QuizDetail = Schemas["QuizDetail"];
export type QuizQuestion = Schemas["QuizQuestion"];
export type AttemptResult = Schemas["AttemptResult"];
export type QuestionResult = Schemas["QuestionResult"];
export type CreateQuizRequest = Schemas["CreateQuizRequest"];

const quizPath = (id: string) => `/v1/quizzes/${encodeURIComponent(id)}`;

export function listQuizzes(spaceId: string, signal?: AbortSignal) {
  return api.get<{ items: QuizSummary[] }>(
    `/v1/quizzes?space_id=${encodeURIComponent(spaceId)}`,
    signal ? { signal } : {},
  );
}

export function getQuiz(id: string, signal?: AbortSignal) {
  return api.get<QuizDetail>(quizPath(id), signal ? { signal } : {});
}

export function createQuiz(request: CreateQuizRequest) {
  // Writing questions takes a while; allow more than the default timeout.
  return api.post<QuizDetail>("/v1/quizzes", request, { timeoutMs: 120_000 });
}

export function deleteQuiz(id: string) {
  return api.delete<void>(quizPath(id));
}

export function submitAttempt(
  id: string,
  answers: { question_id: string; choice: number | null }[],
) {
  return api.post<AttemptResult>(`${quizPath(id)}/attempts`, { answers });
}
