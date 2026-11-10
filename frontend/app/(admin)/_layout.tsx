import { Stack } from "expo-router";

// Admin UI: web only, admin role checked by the backend (F16)
export default function AdminLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: true,
        title: "FlashCard Admin",
      }}
    >
      <Stack.Screen name="dashboard" />
      <Stack.Screen name="users" />
      <Stack.Screen name="documents" />
      <Stack.Screen name="settings" />
      <Stack.Screen name="audit-log" />
    </Stack>
  );
}
