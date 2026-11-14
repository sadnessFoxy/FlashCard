import { useLocalSearchParams } from "expo-router";

import { TakeQuizScreen } from "../../../../src/features/quizzes/TakeQuizScreen";

export default function TakeQuiz() {
  const { quizId } = useLocalSearchParams<{ quizId: string }>();
  return <TakeQuizScreen quizId={quizId} />;
}
