import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { QuizQuestion } from "./api";

const LETTERS = ["A", "B", "C", "D"];

/** One question with its options; the chosen option is highlighted. */
export function QuestionView({
  question,
  choice,
  onChoose,
}: {
  question: QuizQuestion;
  choice: number | undefined;
  onChoose: (choice: number) => void;
}) {
  return (
    <View style={styles.card}>
      <Text style={styles.prompt} testID="quiz-question">
        {question.prompt}
      </Text>
      {question.options.map((option, i) => {
        const selected = choice === i;
        return (
          <Pressable
            key={i}
            accessibilityRole="radio"
            accessibilityState={{ selected }}
            onPress={() => onChoose(i)}
            style={[styles.option, selected && styles.selected]}
            testID={`quiz-option-${i}`}
          >
            <Text style={[styles.letter, selected && styles.selectedText]}>
              {LETTERS[i]}
            </Text>
            <Text style={[styles.optionText, selected && styles.selectedText]}>
              {option}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function optionLetter(index: number | null): string {
  return index === null ? "—" : (LETTERS[index] ?? "?");
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.lg,
  },
  prompt: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "600",
    marginBottom: spacing.sm,
  },
  option: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    padding: spacing.md,
  },
  selected: { backgroundColor: colors.primary, borderColor: colors.primary },
  letter: { color: colors.textMuted, fontSize: fontSize.md, fontWeight: "700" },
  optionText: { color: colors.text, flex: 1, fontSize: fontSize.md },
  selectedText: { color: colors.onPrimary },
});
