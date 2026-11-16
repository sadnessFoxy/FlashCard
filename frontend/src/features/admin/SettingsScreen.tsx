import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Pressable, Text, View } from "react-native";

import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { AdminPage, Row } from "./AdminPage";
import { adminStyles } from "./adminStyles";
import { useAdminSettings, useUpdateSettings } from "./hooks";

const NUMBER_KEYS = [
  "user_daily_query_limit",
  "max_file_size_mb",
  "max_pages",
  "max_documents_per_user",
  "ai_daily_token_budget",
] as const;

/** Screen 24: runtime settings; shows old and new values before saving (A5). */
export function SettingsScreen() {
  const { t } = useTranslation();
  const settings = useAdminSettings();
  const update = useUpdateSettings();
  const [draft, setDraft] = useState<Record<string, string | boolean>>({});

  const values = settings.data?.values ?? {};
  useEffect(() => {
    if (settings.data) setDraft({});
  }, [settings.data]);

  const changes: Record<string, unknown> = {};
  for (const [key, raw] of Object.entries(draft)) {
    const next = typeof raw === "boolean" ? raw : Number(raw);
    if (
      next !== values[key] &&
      !(typeof next === "number" && Number.isNaN(next))
    ) {
      changes[key] = next;
    }
  }
  const changed = Object.keys(changes);
  const aiEnabled = (draft.ai_enabled ?? values.ai_enabled) as boolean;

  return (
    <AdminPage
      title={t("admin.settings.title")}
      loading={settings.isPending}
      error={settings.isError}
    >
      <Row>
        <Text style={adminStyles.strong}>{t("admin.settings.ai_enabled")}</Text>
        <Text style={adminStyles.muted}>{t("admin.settings.aiHint")}</Text>
        <Pressable
          accessibilityRole="switch"
          accessibilityState={{ checked: aiEnabled }}
          onPress={() => setDraft((d) => ({ ...d, ai_enabled: !aiEnabled }))}
          testID="admin-ai-switch"
        >
          <Text style={aiEnabled ? adminStyles.text : adminStyles.danger}>
            {t(aiEnabled ? "admin.overview.aiOn" : "admin.overview.aiOff")}
          </Text>
        </Pressable>
      </Row>
      {NUMBER_KEYS.map((key) => (
        <TextField
          key={key}
          label={`${t(`admin.settings.${key}`)} (${t("admin.settings.default", {
            value: settings.data?.defaults[key],
          })})`}
          value={String(draft[key] ?? values[key] ?? "")}
          onChangeText={(text) => setDraft((d) => ({ ...d, [key]: text }))}
          keyboardType="number-pad"
          testID={`admin-setting-${key}`}
        />
      ))}

      {changed.length > 0 ? (
        <View style={adminStyles.section} testID="admin-settings-diff">
          <Text style={adminStyles.sectionTitle}>
            {t("admin.settings.review")}
          </Text>
          {changed.map((key) => (
            <Text key={key} style={adminStyles.text}>
              {t(`admin.settings.${key}`)}: {String(values[key])} →{" "}
              {String(changes[key])}
            </Text>
          ))}
          <Button
            label={t("admin.settings.save")}
            onPress={() => update.mutate(changes)}
            loading={update.isPending}
            testID="admin-settings-save"
          />
        </View>
      ) : null}
      {update.isError ? (
        <Text style={adminStyles.danger}>{t("admin.settings.invalid")}</Text>
      ) : null}
      <Text style={adminStyles.muted}>{t("admin.settings.applies")}</Text>
    </AdminPage>
  );
}
