import { useRouter } from "expo-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Text, View } from "react-native";

import { ApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { AdminPage, Row } from "./AdminPage";
import { adminStyles } from "./adminStyles";
import {
  useAdminUser,
  useBlockUser,
  useDeleteUser,
  useSetUserQuota,
  useSignOutUser,
  useUnblockUser,
} from "./hooks";
import { ReasonDialog } from "./ReasonDialog";

type Action = "block" | "signOut" | "delete" | null;

/** Screen 22: one user (metadata only, R13) and the admin actions on it; all audited. */
export function UserScreen({ userId }: { userId: string }) {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const user = useAdminUser(userId);
  const block = useBlockUser();
  const unblock = useUnblockUser();
  const signOut = useSignOutUser();
  const setQuota = useSetUserQuota();
  const remove = useDeleteUser();
  const [action, setAction] = useState<Action>(null);
  const [limit, setLimit] = useState("");
  const [days, setDays] = useState("");
  const [error, setError] = useState<string | null>(null);

  const errorText = (e: unknown) =>
    e instanceof ApiError && e.code === "CANNOT_TARGET_SELF"
      ? t("admin.errors.self")
      : t("common.error");

  async function confirm(reason: string) {
    setError(null);
    try {
      if (action === "block") await block.mutateAsync({ id: userId, reason });
      if (action === "signOut") await signOut.mutateAsync(userId);
      if (action === "delete") {
        await remove.mutateAsync({ id: userId, reason });
        router.replace("/admin/users");
      }
      setAction(null);
    } catch (e) {
      setError(errorText(e));
    }
  }

  function saveQuota(clear: boolean) {
    const n = Number(limit);
    const expires =
      Number(days) > 0
        ? new Date(Date.now() + Number(days) * 86_400_000).toISOString()
        : null;
    if (!clear && !(Number.isInteger(n) && n >= 0)) return;
    setQuota.mutate({
      id: userId,
      dailyLimit: clear ? null : n,
      expiresAt: clear ? null : expires,
    });
  }

  const data = user.data;
  return (
    <AdminPage
      title={data?.email ?? t("admin.users.title")}
      loading={user.isPending}
      error={user.isError}
    >
      {data ? (
        <>
          <Row>
            <Text style={adminStyles.text}>
              {t(`admin.users.status.${data.status}`)} · {data.role} ·{" "}
              {data.sign_in_methods.join(", ") || "—"}
            </Text>
            <Text style={adminStyles.muted}>
              {t(
                data.email_verified
                  ? "admin.users.verified"
                  : "admin.users.unverified",
              )}{" "}
              · {t("admin.users.documents", { count: data.document_count })} ·{" "}
              {t("admin.users.questionsToday", { count: data.questions_today })}{" "}
              · {new Date(data.created_at).toLocaleString(i18n.language)}
            </Text>
            <Text style={adminStyles.muted}>{t("admin.users.privacy")}</Text>
          </Row>

          <View style={adminStyles.actions}>
            {data.status === "active" ? (
              <Button
                label={t("admin.users.block")}
                variant="danger"
                onPress={() => setAction("block")}
                testID="admin-block"
              />
            ) : (
              <Button
                label={t("admin.users.unblock")}
                onPress={() => unblock.mutate(userId)}
                loading={unblock.isPending}
                testID="admin-unblock"
              />
            )}
            <Button
              label={t("admin.users.signOut")}
              variant="secondary"
              onPress={() => setAction("signOut")}
              testID="admin-sign-out"
            />
            <Button
              label={t("admin.users.delete")}
              variant="danger"
              onPress={() => setAction("delete")}
              testID="admin-delete"
            />
          </View>

          <View style={adminStyles.section}>
            <Text style={adminStyles.sectionTitle}>
              {t("admin.users.quotaTitle")}
            </Text>
            <Text style={adminStyles.muted}>
              {data.quota_override
                ? t("admin.users.quotaCurrent", {
                    limit: data.quota_override.daily_limit,
                    until: data.quota_override.expires_at
                      ? new Date(
                          data.quota_override.expires_at,
                        ).toLocaleDateString(i18n.language)
                      : t("admin.users.noExpiry"),
                  })
                : t("admin.users.quotaDefault")}
            </Text>
            <TextField
              label={t("admin.users.quotaLimit")}
              value={limit}
              onChangeText={setLimit}
              keyboardType="number-pad"
              testID="admin-quota-limit"
            />
            <TextField
              label={t("admin.users.quotaDays")}
              value={days}
              onChangeText={setDays}
              keyboardType="number-pad"
              testID="admin-quota-days"
            />
            <View style={adminStyles.actions}>
              <Button
                label={t("common.save")}
                onPress={() => saveQuota(false)}
                loading={setQuota.isPending}
                testID="admin-quota-save"
              />
              {data.quota_override ? (
                <Button
                  label={t("admin.users.quotaClear")}
                  variant="secondary"
                  onPress={() => saveQuota(true)}
                />
              ) : null}
            </View>
          </View>
        </>
      ) : null}

      <ReasonDialog
        visible={action !== null}
        title={action ? t(`admin.users.confirm.${action}.title`) : ""}
        message={action ? t(`admin.users.confirm.${action}.message`) : ""}
        confirmLabel={t("common.confirm")}
        needsReason={action === "block" || action === "delete"}
        busy={block.isPending || signOut.isPending || remove.isPending}
        error={error}
        onConfirm={(reason) => void confirm(reason)}
        onClose={() => {
          setAction(null);
          setError(null);
        }}
      />
    </AdminPage>
  );
}
