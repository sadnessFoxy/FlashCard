import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { colors, fontSize, spacing } from "../../theme/tokens";
import { Button } from "../ui/Button";

interface Props {
  /** Shown when the backend could not be reached; null while loading. */
  onRetry?: (() => void) | null;
}

export function SplashScreen({ onRetry = null }: Props) {
  const { t } = useTranslation();
  return (
    <View style={styles.container} testID="splash">
      {onRetry ? (
        <>
          <Text style={styles.text}>{t("splash.unreachable")}</Text>
          <Button
            label={t("common.retry")}
            onPress={onRetry}
            testID="splash-retry"
          />
        </>
      ) : (
        <>
          <ActivityIndicator color={colors.primary} />
          <Text style={styles.text}>{t("common.loading")}</Text>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    backgroundColor: colors.background,
    flex: 1,
    gap: spacing.lg,
    justifyContent: "center",
    padding: spacing.xl,
  },
  text: { color: colors.textMuted, fontSize: fontSize.md, textAlign: "center" },
});
