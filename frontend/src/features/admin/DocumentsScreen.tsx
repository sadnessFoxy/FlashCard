import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Text, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { ChipGroup } from "../../components/ui/ChipGroup";
import { AdminPage, Row } from "./AdminPage";
import { adminStyles } from "./adminStyles";
import { useAdminDocuments, useRetryDocument } from "./hooks";

const FILTERS = [
  "ALL",
  "FAILED",
  "PAUSED_QUOTA",
  "QUEUED",
  "PROCESSING",
  "READY",
];
const RETRYABLE = new Set(["FAILED", "PAUSED_QUOTA"]);

/** Screen 23: documents and their latest job, retry failed or paused ones (A4). */
export function DocumentsScreen() {
  const { t, i18n } = useTranslation();
  const [filter, setFilter] = useState("FAILED");
  const documents = useAdminDocuments(filter === "ALL" ? null : filter);
  const retry = useRetryDocument();

  return (
    <AdminPage title={t("admin.documents.title")} error={documents.isError}>
      <ChipGroup
        options={FILTERS.map((f) => ({
          value: f,
          label:
            f === "ALL" ? t("admin.documents.all") : t(`documents.status.${f}`),
        }))}
        value={filter}
        onChange={setFilter}
        testID="admin-doc-filter"
      />
      {documents.data?.items.length === 0 ? (
        <Text style={adminStyles.muted}>{t("admin.documents.empty")}</Text>
      ) : null}
      {documents.data?.items.map((doc) => (
        <Row key={doc.id} testID={`admin-doc-${doc.id}`}>
          <Text style={adminStyles.strong}>
            {doc.filename} · {t(`documents.status.${doc.status}`)}
          </Text>
          <Text style={adminStyles.muted}>
            {doc.owner_email} · {doc.file_kind}
            {doc.text_source === "ai_ocr" ? " (scan)" : ""} ·{" "}
            {t("documents.detail.pages", { count: doc.page_count })} ·{" "}
            {new Date(doc.updated_at).toLocaleString(i18n.language)}
          </Text>
          {doc.error_code || doc.last_job?.last_error_code ? (
            <Text style={adminStyles.danger}>
              {doc.error_code ?? ""} {doc.last_job?.last_error_code ?? ""}
              {doc.last_job
                ? ` · ${t("admin.documents.attempts", { count: doc.last_job.attempts })}`
                : ""}
            </Text>
          ) : null}
          {RETRYABLE.has(doc.status) ? (
            <View style={adminStyles.actions}>
              <Button
                label={t("documents.retry")}
                variant="secondary"
                onPress={() => retry.mutate(doc.id)}
                loading={retry.isPending && retry.variables === doc.id}
                testID={`admin-retry-${doc.id}`}
              />
            </View>
          ) : null}
        </Row>
      ))}
    </AdminPage>
  );
}
