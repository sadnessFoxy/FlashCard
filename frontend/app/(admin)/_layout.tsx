import { Stack } from "expo-router";

// Giao diện quản trị: chỉ dùng trên web, kiểm tra vai trò admin
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
