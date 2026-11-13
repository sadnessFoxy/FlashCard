import * as DocumentPicker from "expo-document-picker";
import { useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { Dialog } from "../../components/feedback/Dialog";
import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import { uuidv4 } from "../../utils/uuid";
import type { DocumentItem, DocumentStatus, PickedFile } from "./api";
import {
  useAiConsent,
  useDocuments,
  useGiveAiConsent,
  useUploadDocument,
} from "./hooks";
import { uploadErrorMessage } from "./uploadError";

const MAX_MB = 20;

const BADGE: Record<DocumentStatus, { fg: string; bg: string }> = {
  UPLOADED: { fg: "#1e40af", bg: "#dbeafe" },
  QUEUED: { fg: "#1e40af", bg: "#dbeafe" },
  PROCESSING: { fg: "#1e40af", bg: "#dbeafe" },
  READY: { fg: "#166534", bg: "#dcfce7" },
  FAILED: { fg: "#991b1b", bg: "#fee2e2" },
  PAUSED_QUOTA: { fg: "#92400e", bg: "#fef3c7" },
  DELETING: { fg: "#4b5563", bg: "#f3f4f6" },
};

interface PendingUpload {
  file: PickedFile;
  key: string; // reused on retry so a lost response cannot create a duplicate
}

function DocumentRow({ doc }: { doc: DocumentItem }) {
  const { t, i18n } = useTranslation();
  const badge = BADGE[doc.status];
  return (
    <View style={styles.row} testID={`document-${doc.id}`}>
      <View style={styles.rowText}>
        <Text style={styles.rowTitle} numberOfLines={2}>
          {doc.filename}
        </Text>
        <Text style={styles.muted}>
          {t("documents.meta", {
            pages: doc.page_count,
            date: new Date(doc.created_at).toLocaleDateString(i18n.language),
          })}
        </Text>
        {doc.status === "FAILED" && doc.error_code && (
          <Text style={styles.errorText}>
            {t(`documents.failure.${doc.error_code}`)}
          </Text>
        )}
        {doc.status === "PAUSED_QUOTA" && (
          <Text style={styles.muted}>{t("documents.pausedHint")}</Text>
        )}
      </View>
      <View style={[styles.badge, { backgroundColor: badge.bg }]}>
        <Text style={[styles.badgeText, { color: badge.fg }]}>
          {t(`documents.status.${doc.status}`)}
        </Text>
      </View>
    </View>
  );
}

export function DocumentsTab({ spaceId }: { spaceId: string }) {
  const { t } = useTranslation();
  const documents = useDocuments(spaceId);
  const consent = useAiConsent();
  const giveConsent = useGiveAiConsent();
  const upload = useUploadDocument(spaceId);
  const [askConsent, setAskConsent] = useState(false);
  const [pending, setPending] = useState<PendingUpload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const atLimit = documents.data
    ? documents.data.total_documents >= documents.data.max_documents
    : false;

  async function send(next: PendingUpload) {
    setPending(next);
    setError(null);
    try {
      await upload.mutateAsync(next);
      setPending(null);
    } catch (e) {
      setError(uploadErrorMessage(e, t));
    }
  }

  async function pick() {
    setError(null);
    const result = await DocumentPicker.getDocumentAsync({
      type: "application/pdf",
      copyToCacheDirectory: true,
      multiple: false,
    });
    if (result.canceled || !result.assets[0]) return;
    const asset = result.assets[0];
    if (asset.size && asset.size > MAX_MB * 1024 * 1024) {
      setError(t("documents.errors.tooLarge", { mb: MAX_MB }));
      return;
    }
    await send({
      file: {
        name: asset.name,
        size: asset.size,
        mimeType: asset.mimeType,
        uri: asset.uri,
        file: asset.file,
      },
      key: uuidv4(),
    });
  }

  function startUpload() {
    if (consent.data?.ok) void pick();
    else setAskConsent(true);
  }

  async function accept() {
    if (!consent.data) return;
    await giveConsent.mutateAsync(consent.data.version);
    setAskConsent(false);
    void pick();
  }

  if (documents.isPending) {
    return (
      <View style={styles.center} testID="documents-loading">
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  if (documents.isError) {
    return (
      <View style={styles.center} testID="documents-error">
        <Text style={styles.muted}>{t("documents.loadError")}</Text>
        <Button
          label={t("common.retry")}
          variant="secondary"
          onPress={() => void documents.refetch()}
        />
      </View>
    );
  }

  const { items, total_documents, max_documents } = documents.data;

  return (
    <View style={styles.container}>
      <View style={styles.toolbar}>
        <Text style={styles.muted} testID="documents-count">
          {t("documents.count", { count: total_documents, max: max_documents })}
        </Text>
        <Button
          label={t("documents.upload")}
          onPress={startUpload}
          loading={upload.isPending}
          disabled={atLimit || consent.isPending}
          testID="documents-upload"
        />
      </View>
      {atLimit && (
        <Text style={styles.muted}>
          {t("documents.errors.limit", { max: max_documents })}
        </Text>
      )}

      {error && (
        <View style={styles.errorBox} testID="documents-upload-error">
          <Text style={styles.errorText}>{error}</Text>
          {pending && (
            <Button
              label={t("common.retry")}
              variant="secondary"
              onPress={() => void send(pending)}
            />
          )}
        </View>
      )}

      {items.length === 0 ? (
        <View style={styles.center} testID="documents-empty">
          <Text style={styles.emptyTitle}>{t("documents.emptyTitle")}</Text>
          <Text style={styles.muted}>
            {t("documents.emptyHint", { mb: MAX_MB })}
          </Text>
        </View>
      ) : (
        <View style={styles.list}>
          {items.map((doc) => (
            <DocumentRow key={doc.id} doc={doc} />
          ))}
        </View>
      )}

      <Dialog
        visible={askConsent}
        title={t("documents.consent.title")}
        onDismiss={() => setAskConsent(false)}
        testID="documents-consent"
      >
        <Text style={styles.body}>{t("documents.consent.body")}</Text>
        <View style={styles.actions}>
          <Button
            label={t("common.cancel")}
            variant="secondary"
            onPress={() => setAskConsent(false)}
          />
          <Button
            label={t("documents.consent.accept")}
            onPress={() => void accept()}
            loading={giveConsent.isPending}
            testID="documents-consent-accept"
          />
        </View>
      </Dialog>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.md },
  toolbar: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  center: {
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.xl,
  },
  emptyTitle: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  body: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  list: { gap: spacing.sm },
  row: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    padding: spacing.lg,
  },
  rowText: { flex: 1, gap: spacing.xs },
  rowTitle: { color: colors.text, fontSize: fontSize.md, fontWeight: "600" },
  badge: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 },
  badgeText: { fontSize: fontSize.sm, fontWeight: "600" },
  errorBox: {
    backgroundColor: colors.dangerBg,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.md,
  },
  errorText: { color: colors.danger, fontSize: fontSize.sm },
  actions: {
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "flex-end",
  },
});
