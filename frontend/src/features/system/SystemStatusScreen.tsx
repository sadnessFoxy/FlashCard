import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useTranslation } from "react-i18next";

import type { CheckErrorCode, DatabaseCheck, DependencyCheck } from "./api";
import { useSystemStatus } from "./useSystemStatus";

type Tone = "ok" | "warn" | "bad";

const TONE_COLORS: Record<Tone, { fg: string; bg: string }> = {
  ok: { fg: "#166534", bg: "#dcfce7" },
  warn: { fg: "#92400e", bg: "#fef3c7" },
  bad: { fg: "#991b1b", bg: "#fee2e2" },
};

interface RowProps {
  label: string;
  up: boolean;
  details: string[];
  testID: string;
}

function StatusRow({ label, up, details, testID }: RowProps) {
  const { t } = useTranslation();
  const tone = TONE_COLORS[up ? "ok" : "bad"];
  return (
    <View style={styles.row} testID={testID}>
      <View style={styles.rowText}>
        <Text style={styles.rowLabel}>{label}</Text>
        {details.length > 0 && (
          <Text style={styles.rowDetails}>{details.join(" · ")}</Text>
        )}
      </View>
      <View style={[styles.badge, { backgroundColor: tone.bg }]}>
        <Text style={[styles.badgeText, { color: tone.fg }]}>
          {t(up ? "system.state.up" : "system.state.down")}
        </Text>
      </View>
    </View>
  );
}

function useCheckDetails() {
  const { t } = useTranslation();
  return (
    check: DependencyCheck | DatabaseCheck,
    extra: string[] = [],
  ): string[] => {
    const details = [
      t("system.latency", { ms: Math.round(check.latency_ms) }),
      ...extra,
    ];
    if (check.error_code) {
      details.push(
        t(`system.errorCodes.${check.error_code satisfies CheckErrorCode}`),
      );
    }
    return details;
  };
}

interface Props {
  apiUrl: string;
}

export function SystemStatusScreen({ apiUrl }: Props) {
  const { t, i18n } = useTranslation();
  const {
    data,
    isPending,
    isError,
    isFetching,
    refetch,
    dataUpdatedAt,
    errorUpdatedAt,
  } = useSystemStatus();
  const checkDetails = useCheckDetails();

  const unreachable = isError;
  const overallTone: Tone = unreachable
    ? "bad"
    : data?.status === "ok"
      ? "ok"
      : "warn";
  const overallKey = unreachable
    ? "system.overall.unreachable"
    : data?.status === "ok"
      ? "system.overall.ok"
      : "system.overall.degraded";
  const checkedAt = unreachable ? errorUpdatedAt : dataUpdatedAt;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        {t("system.title")}
      </Text>
      <Text style={styles.subtitle}>{t("system.subtitle")}</Text>

      {isPending ? (
        <View style={styles.center} testID="system-status-loading">
          <ActivityIndicator />
          <Text style={styles.muted}>{t("common.loading")}</Text>
        </View>
      ) : (
        <>
          <View
            style={[
              styles.banner,
              { backgroundColor: TONE_COLORS[overallTone].bg },
            ]}
            testID="system-status-overall"
          >
            <Text
              style={[
                styles.bannerText,
                { color: TONE_COLORS[overallTone].fg },
              ]}
            >
              {t(overallKey)}
            </Text>
            {unreachable && (
              <Text style={[styles.bannerHint, { color: TONE_COLORS.bad.fg }]}>
                {t("system.unreachableHint", { url: apiUrl })}
              </Text>
            )}
          </View>

          <View style={styles.card}>
            <StatusRow
              label={t("system.components.api")}
              up={!unreachable}
              details={
                data ? [t("system.version", { version: data.version })] : []
              }
              testID="system-status-api"
            />
            {data && (
              <>
                <StatusRow
                  label={t("system.components.database")}
                  up={data.checks.database.status === "up"}
                  details={checkDetails(
                    data.checks.database,
                    data.checks.database.pgvector_version
                      ? [
                          t("system.pgvector", {
                            version: data.checks.database.pgvector_version,
                          }),
                        ]
                      : [],
                  )}
                  testID="system-status-database"
                />
                <StatusRow
                  label={t("system.components.redis")}
                  up={data.checks.redis.status === "up"}
                  details={checkDetails(data.checks.redis)}
                  testID="system-status-redis"
                />
              </>
            )}
          </View>

          {checkedAt > 0 && (
            <Text style={styles.muted}>
              {t("system.checkedAt", {
                time: new Date(checkedAt).toLocaleTimeString(i18n.language),
              })}
            </Text>
          )}
        </>
      )}

      <Pressable
        accessibilityRole="button"
        onPress={() => void refetch()}
        disabled={isFetching}
        style={({ pressed }) => [
          styles.button,
          (pressed || isFetching) && styles.buttonPressed,
        ]}
        testID="system-status-refresh"
      >
        <Text style={styles.buttonText}>{t("system.refresh")}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    gap: 16,
    maxWidth: 640,
    width: "100%",
    alignSelf: "center",
  },
  title: { fontSize: 24, fontWeight: "700", color: "#111827" },
  subtitle: { fontSize: 15, color: "#4b5563" },
  center: { alignItems: "center", gap: 8, paddingVertical: 32 },
  muted: { fontSize: 13, color: "#6b7280" },
  banner: { borderRadius: 12, padding: 16, gap: 4 },
  bannerText: { fontSize: 16, fontWeight: "600" },
  bannerHint: { fontSize: 14 },
  card: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    backgroundColor: "#ffffff",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  rowText: { flex: 1, gap: 2 },
  rowLabel: { fontSize: 15, fontWeight: "600", color: "#111827" },
  rowDetails: { fontSize: 13, color: "#6b7280" },
  badge: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 },
  badgeText: { fontSize: 13, fontWeight: "600" },
  button: {
    alignSelf: "flex-start",
    backgroundColor: "#2563eb",
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  buttonPressed: { opacity: 0.7 },
  buttonText: { color: "#ffffff", fontSize: 15, fontWeight: "600" },
});
