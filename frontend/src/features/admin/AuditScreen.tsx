import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Text } from "react-native";

import { ChipGroup } from "../../components/ui/ChipGroup";
import { AdminPage, Row } from "./AdminPage";
import { adminStyles } from "./adminStyles";
import { useAudit } from "./hooks";

const ACTIONS = [
  "ALL",
  "user.block",
  "user.unblock",
  "user.sign_out",
  "user.quota",
  "user.delete",
  "document.retry",
  "settings.update",
];

/** Screen 25: the audit log, read only (A7). */
export function AuditScreen() {
  const { t, i18n } = useTranslation();
  const [action, setAction] = useState("ALL");
  const entries = useAudit(action === "ALL" ? null : action);

  return (
    <AdminPage title={t("admin.audit.title")} error={entries.isError}>
      <ChipGroup
        options={ACTIONS.map((a) => ({
          value: a,
          label: a === "ALL" ? t("admin.documents.all") : a,
        }))}
        value={action}
        onChange={setAction}
        testID="admin-audit-filter"
      />
      {entries.data?.items.length === 0 ? (
        <Text style={adminStyles.muted}>{t("admin.audit.empty")}</Text>
      ) : null}
      {entries.data?.items.map((entry) => (
        <Row key={entry.id} testID={`admin-audit-${entry.id}`}>
          <Text style={adminStyles.strong}>
            {entry.action} · {entry.target_type} {entry.target_id ?? ""}
          </Text>
          <Text style={adminStyles.muted}>
            {entry.actor_email} ·{" "}
            {new Date(entry.created_at).toLocaleString(i18n.language)}
          </Text>
          {entry.before || entry.after ? (
            <Text style={adminStyles.text}>
              {JSON.stringify(entry.before)} → {JSON.stringify(entry.after)}
            </Text>
          ) : null}
          {entry.reason ? (
            <Text style={adminStyles.text}>
              {t("admin.reason")}: {entry.reason}
            </Text>
          ) : null}
        </Row>
      ))}
    </AdminPage>
  );
}
