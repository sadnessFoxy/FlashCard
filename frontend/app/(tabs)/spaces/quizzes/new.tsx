import { useLocalSearchParams } from "expo-router";

import { CreateQuizScreen } from "../../../../src/features/quizzes/CreateQuizScreen";

export default function NewQuiz() {
  const { spaceId } = useLocalSearchParams<{ spaceId: string }>();
  return <CreateQuizScreen spaceId={spaceId} />;
}
