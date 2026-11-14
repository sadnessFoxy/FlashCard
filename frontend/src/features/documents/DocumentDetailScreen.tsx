import { useRouter } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useTranslation } from "react-i18next";

import { ApiError } from "../../api/errors";
import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { useSpaces } from "../spaces/hooks";
import {
  useDeleteDocument,
  useDocument,
  useMoveDocument,
  useRetryDocument,
} from "./hooks";
import { StatusBadge } from "./StatusBadge";

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentDetailScreen({ id }: { id: string }) {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const document = useDocument(id);
  const spaces = useSpaces();
  const retry = useRetryDocument(id);
  const move = useMoveDocument(id);
  const remove = useDeleteDocument(id);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [moving, setMoving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const back = (spaceId?: string) =>
    spaceId
      ? router.replace({ pathname: "/spaces/[id]", params: { id: spaceId } })
      : router.replace("/spaces");

  if (document.isPending) {
    return (
      <View style={styles.center} testID="document-loading">
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  if (document.isError) {
    const missing =
      document.error instanceof ApiError && document.error.code === "NOT_FOUND";
    return (
      <View style={styles.center} testID="document-missing">
        <Text style={styles.muted}>
          {t(missing ? "documents.notFound" : "documents.loadError")}
        </Text>
        <Button
          label={t("spaces.backToList")}
          variant="secondary"
          onPress={() => back()}
        />
      </View>
    );
  }

  const doc = document.data;
  const retryable = doc.status === "FAILED" || doc.status === "PAUSED_QUOTA";
  const otherSpaces = (spaces.data ?? []).filter((s) => s.id !== doc.space_id);

  async function run(action: () => Promise<unknown>) {
    setActionError(null);
    try {
      await action();
    } catch {
      setActionError(t("common.error"));
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable accessibilityRole="link" onPress={() => back(doc.space_id)}>
        <Text style={styles.link}>{t("documents.backToSpace")}</Text>
      </Pressable>

      <Text
        style={styles.title}
        accessibilityRole="header"
        testID="document-title"
      >
        {doc.filename}
      </Text>
      <StatusBadge status={doc.status} />

      <View style={styles.card}>
        <Text style={styles.meta}>
          {t("documents.detail.pages", { count: doc.page_count })}
        </Text>
        <Text style={styles.meta}>
          {t("documents.detail.size", { size: formatSize(doc.size_bytes) })}
        </Text>
        <Text style={styles.meta}>
          {t("documents.detail.uploaded", {
            date: new Date(doc.created_at).toLocaleString(i18n.language),
          })}
        </Text>
        {doc.status === "FAILED" && doc.error_code && (
          <Text style={styles.error}>
            {t(`documents.failure.${doc.error_code}`)}
          </Text>
        )}
        {doc.status === "PAUSED_QUOTA" && (
          <Text style={styles.meta}>{t("documents.pausedHint")}</Text>
        )}
      </View>

      {actionError && <Text style={styles.error}>{actionError}</Text>}

      <View style={styles.actions}>
        {retryable && (
          <Button
            label={t("documents.retry")}
            onPress={() => void run(() => retry.mutateAsync())}
            loading={retry.isPending}
            testID="document-retry"
          />
        )}
        <Button
          label={t("documents.move")}
          variant="secondary"
          onPress={() => setMoving(true)}
          testID="document-move"
        />
        <Button
          label={t("common.delete")}
          variant="danger"
          onPress={() => setConfirmDelete(true)}
          testID="document-delete"
        />
      </View>

      {doc.status === "READY" ? (
        <View style={styles.shortcuts}>
          <Button
            label={t("summaries.open")}
            variant="secondary"
            onPress={() =>
              router.push({
                pathname: "/spaces/documents/summary/[documentId]",
                params: { documentId: doc.id },
              })
            }
            testID="document-summaries"
          />
          <Button
            label={t("cards.generate")}
            variant="secondary"
            onPress={() =>
              router.push({
                pathname: "/spaces/decks/generate",
                params: { spaceId: doc.space_id },
              })
            }
          />
          <Button
            label={t("quizzes.create")}
            variant="secondary"
            onPress={() =>
              router.push({
                pathname: "/spaces/quizzes/new",
                params: { spaceId: doc.space_id },
              })
            }
          />
        </View>
      ) : null}

      <Dialog
        visible={confirmDelete}
        title={t("documents.deleteTitle", { name: doc.filename })}
        onDismiss={() => setConfirmDelete(false)}
        testID="document-delete-dialog"
      >
        <Text style={styles.body}>{t("documents.deleteWarning")}</Text>
        <View style={styles.dialogActions}>
          <Button
            label={t("common.cancel")}
            variant="secondary"
            onPress={() => setConfirmDelete(false)}
          />
          <Button
            label={t("common.delete")}
            variant="danger"
            loading={remove.isPending}
            onPress={() =>
              void run(async () => {
                await remove.mutateAsync();
                setConfirmDelete(false);
                back(doc.space_id);
              })
            }
            testID="document-delete-confirm"
          />
        </View>
      </Dialog>

      <Dialog
        visible={moving}
        title={t("documents.moveTitle")}
        onDismiss={() => setMoving(false)}
        testID="document-move-dialog"
      >
        {otherSpaces.length === 0 ? (
          <Text style={styles.body}>{t("documents.moveNoSpaces")}</Text>
        ) : (
          otherSpaces.map((s) => (
            <Button
              key={s.id}
              label={s.name}
              variant="secondary"
              onPress={() =>
                void run(async () => {
                  await move.mutateAsync(s.id);
                  setMoving(false);
                })
              }
              testID={`move-to-${s.id}`}
            />
          ))
        )}
        <Button
          label={t("common.cancel")}
          variant="secondary"
          onPress={() => setMoving(false)}
        />
      </Dialog>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    gap: spacing.lg,
    maxWidth: 720,
    padding: spacing.xl,
    width: "100%",
  },
  center: {
    alignItems: "center",
    flex: 1,
    gap: spacing.md,
    justifyContent: "center",
    padding: spacing.xl,
  },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.lg,
  },
  meta: { color: colors.textMuted, fontSize: fontSize.md },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  body: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  error: { color: colors.danger, fontSize: fontSize.sm },
  actions: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  dialogActions: {
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "flex-end",
  },
  shortcuts: { gap: spacing.sm },
});
