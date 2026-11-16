import { useRouter } from "expo-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Text } from "react-native";

import { TextField } from "../../components/ui/TextField";
import { AdminPage, Row } from "./AdminPage";
import { adminStyles } from "./adminStyles";
import { useAdminUsers } from "./hooks";

/** Screen 21: users with sign-in methods, status, documents and today's usage (A3). */
export function UsersScreen() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const users = useAdminUsers(query);

  return (
    <AdminPage title={t("admin.users.title")} error={users.isError}>
      <TextField
        label={t("admin.users.search")}
        value={query}
        onChangeText={setQuery}
        autoCapitalize="none"
        testID="admin-users-search"
      />
      {users.data ? (
        <>
          <Text style={adminStyles.muted}>
            {t("admin.users.total", { count: users.data.total })}
          </Text>
          {users.data.items.map((user) => (
            <Row
              key={user.id}
              onPress={() =>
                router.push({
                  pathname: "/admin/users/[userId]",
                  params: { userId: user.id },
                })
              }
              testID={`admin-user-${user.id}`}
            >
              <Text style={adminStyles.strong}>
                {user.email}
                {user.role === "admin" ? ` · ${t("admin.users.admin")}` : ""}
              </Text>
              <Text
                style={
                  user.status === "blocked"
                    ? adminStyles.danger
                    : adminStyles.muted
                }
              >
                {t(`admin.users.status.${user.status}`)} ·{" "}
                {user.sign_in_methods.join(", ") || "—"} ·{" "}
                {t("admin.users.documents", { count: user.document_count })} ·{" "}
                {t("admin.users.questionsToday", {
                  count: user.questions_today,
                })}{" "}
                · {new Date(user.created_at).toLocaleDateString(i18n.language)}
              </Text>
            </Row>
          ))}
        </>
      ) : null}
    </AdminPage>
  );
}
