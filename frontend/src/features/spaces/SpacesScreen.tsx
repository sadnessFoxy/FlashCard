import { useRouter } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useTranslation } from "react-i18next";

import { Button } from "../../components/ui/Button";
import { colors, fontSize, radius, spacing } from "../../theme/tokens";
import type { Space } from "./api";
import {
  useCreateSpace,
  useDeleteSpace,
  useRenameSpace,
  useSpaces,
} from "./hooks";
import { VerifyEmailBanner } from "../auth/VerifyEmailBanner";
import { DeleteSpaceDialog, SpaceNameDialog } from "./SpaceDialogs";

export function SpacesScreen() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const spaces = useSpaces();
  const create = useCreateSpace();
  const rename = useRenameSpace();
  const remove = useDeleteSpace();

  const [creating, setCreating] = useState(false);
  const [renaming, setRenaming] = useState<Space | null>(null);
  const [deleting, setDeleting] = useState<Space | null>(null);

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(i18n.language);

  function renderBody() {
    if (spaces.isPending) {
      return (
        <View style={styles.center} testID="spaces-loading">
          <ActivityIndicator color={colors.primary} />
        </View>
      );
    }
    if (spaces.isError) {
      return (
        <View style={styles.center} testID="spaces-error">
          <Text style={styles.muted}>{t("spaces.loadError")}</Text>
          <Button
            label={t("common.retry")}
            variant="secondary"
            onPress={() => void spaces.refetch()}
          />
        </View>
      );
    }
    if (spaces.data.length === 0) {
      return (
        <View style={styles.center} testID="spaces-empty">
          <Text style={styles.emptyTitle}>{t("spaces.emptyTitle")}</Text>
          <Text style={styles.muted}>{t("spaces.emptyHint")}</Text>
          <Button
            label={t("spaces.createFirst")}
            onPress={() => setCreating(true)}
          />
        </View>
      );
    }
    return (
      <FlatList
        data={spaces.data}
        keyExtractor={(s) => s.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <View style={styles.card} testID={`space-${item.id}`}>
            <Pressable
              accessibilityRole="link"
              onPress={() =>
                router.push({
                  pathname: "/spaces/[id]",
                  params: { id: item.id },
                })
              }
              style={styles.cardMain}
            >
              <Text style={styles.cardTitle} numberOfLines={2}>
                {item.name}
              </Text>
              <Text style={styles.muted}>
                {t("spaces.updatedAt", { date: formatDate(item.updated_at) })}
              </Text>
            </Pressable>
            <View style={styles.cardActions}>
              <Pressable
                accessibilityRole="button"
                onPress={() => setRenaming(item)}
                hitSlop={6}
              >
                <Text style={styles.link}>{t("spaces.rename")}</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                onPress={() => setDeleting(item)}
                hitSlop={6}
              >
                <Text style={styles.linkDanger}>{t("common.delete")}</Text>
              </Pressable>
            </View>
          </View>
        )}
      />
    );
  }

  return (
    <View style={styles.container}>
      <VerifyEmailBanner />
      <View style={styles.header}>
        <Text style={styles.title} accessibilityRole="header">
          {t("tabs.spaces")}
        </Text>
        {spaces.data && spaces.data.length > 0 && (
          <Button
            label={t("spaces.create")}
            onPress={() => setCreating(true)}
            testID="spaces-create"
          />
        )}
      </View>

      {renderBody()}

      <SpaceNameDialog
        visible={creating}
        mode="create"
        onSubmit={(name) => create.mutateAsync(name)}
        onClose={() => setCreating(false)}
      />
      <SpaceNameDialog
        visible={renaming !== null}
        mode="rename"
        initialName={renaming?.name ?? ""}
        onSubmit={(name) =>
          rename.mutateAsync({ id: renaming?.id ?? "", name })
        }
        onClose={() => setRenaming(null)}
      />
      <DeleteSpaceDialog
        spaceName={deleting?.name ?? null}
        onConfirm={() => remove.mutateAsync(deleting?.id ?? "")}
        onClose={() => setDeleting(null)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "center",
    flex: 1,
    gap: spacing.lg,
    maxWidth: 720,
    padding: spacing.xl,
    width: "100%",
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  title: { color: colors.text, fontSize: fontSize.xl, fontWeight: "700" },
  center: {
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.xxl,
  },
  emptyTitle: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
  muted: {
    color: colors.textMuted,
    fontSize: fontSize.sm,
    textAlign: "center",
  },
  list: { gap: spacing.md },
  card: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    padding: spacing.lg,
  },
  cardMain: { flex: 1, gap: spacing.xs },
  cardTitle: { color: colors.text, fontSize: fontSize.lg, fontWeight: "600" },
  cardActions: { flexDirection: "row", gap: spacing.lg },
  link: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
  linkDanger: {
    color: colors.danger,
    fontSize: fontSize.sm,
    fontWeight: "600",
  },
});
