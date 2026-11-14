import { useEffect, useState } from "react";

import { loadDraft, removeDraft, saveDraft } from "../../storage/drafts";

export type Answers = Record<string, number>;

interface Draft {
  answers: Answers;
  index: number;
}

const draftKey = (quizId: string) => `quiz.${quizId}`;

/** Answers in progress; an unfinished quiz can be saved on the device and resumed. */
export function useQuizAnswers(quizId: string) {
  const [answers, setAnswers] = useState<Answers>({});
  const [index, setIndex] = useState(0);
  const [resumed, setResumed] = useState(false);

  useEffect(() => {
    let active = true;
    void loadDraft<Draft>(draftKey(quizId)).then((draft) => {
      if (active && draft) {
        setAnswers(draft.answers);
        setIndex(draft.index);
        setResumed(true);
      }
    });
    return () => {
      active = false;
    };
  }, [quizId]);

  return {
    answers,
    index,
    resumed,
    setIndex,
    choose: (questionId: string, choice: number) =>
      setAnswers((prev) => ({ ...prev, [questionId]: choice })),
    saveForLater: () => saveDraft(draftKey(quizId), { answers, index }),
    discard: async () => {
      await removeDraft(draftKey(quizId));
      setAnswers({});
      setIndex(0);
      setResumed(false);
    },
  };
}
