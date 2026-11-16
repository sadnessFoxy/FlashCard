import { useTranslation } from "react-i18next";
import { Text, View } from "react-native";

import { AdminPage, Stat } from "./AdminPage";
import { adminStyles } from "./adminStyles";
import { useOverview } from "./hooks";

const BUDGET_ALERT_PERCENT = 80;

/** Screen 20: usage, documents, AI and queue at a glance (A2). */
export function OverviewScreen() {
  const { t } = useTranslation();
  const overview = useOverview();
  const data = overview.data;

  return (
    <AdminPage
      title={t("admin.overview.title")}
      loading={overview.isPending}
      error={overview.isError}
    >
      {data ? (
        <>
          <View style={adminStyles.grid}>
            <Stat label={t("admin.overview.users")} value={data.users_total} />
            <Stat
              label={t("admin.overview.activeToday")}
              value={data.users_active_today}
            />
            <Stat
              label={t("admin.overview.questionsToday")}
              value={data.questions_today}
            />
            <Stat
              label={t("admin.overview.aiCalls")}
              value={data.ai_calls_today}
            />
            <Stat
              label={t("admin.overview.aiFailures")}
              value={data.ai_failures_today}
              alert={data.ai_failures_today > 0}
            />
            <Stat
              label={t("admin.overview.tokens")}
              value={data.ai_tokens_today.toLocaleString()}
            />
            {data.ai_budget_used_percent !== null ? (
              <Stat
                label={t("admin.overview.budget")}
                value={`${data.ai_budget_used_percent}%`}
                alert={data.ai_budget_used_percent >= BUDGET_ALERT_PERCENT}
              />
            ) : null}
            <Stat
              label={t("admin.overview.ai")}
              value={t(
                data.ai_enabled
                  ? "admin.overview.aiOn"
                  : "admin.overview.aiOff",
              )}
              alert={!data.ai_enabled}
            />
            <Stat
              label={t("admin.overview.breaker")}
              value={t(`admin.overview.breakerState.${data.circuit_state}`)}
              alert={data.circuit_state !== "closed"}
            />
            <Stat label={t("admin.overview.queue")} value={data.queue_length} />
          </View>
          <View style={adminStyles.section}>
            <Text style={adminStyles.sectionTitle}>
              {t("admin.overview.documents")}
            </Text>
            <View style={adminStyles.grid}>
              {Object.entries(data.documents_by_status).map(
                ([status, count]) => (
                  <Stat
                    key={status}
                    label={t(`documents.status.${status}`)}
                    value={count}
                    alert={status === "FAILED" || status === "PAUSED_QUOTA"}
                  />
                ),
              )}
            </View>
          </View>
          <Text style={adminStyles.muted}>{t("admin.overview.note")}</Text>
        </>
      ) : null}
    </AdminPage>
  );
}
