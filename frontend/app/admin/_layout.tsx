import { Stack } from "expo-router";

import { AdminGate } from "../../src/features/admin/AdminGate";

export default function AdminLayout() {
  return (
    <AdminGate>
      <Stack screenOptions={{ headerShown: false }} />
    </AdminGate>
  );
}
