import { useLocalSearchParams } from "expo-router";

import { UserScreen } from "../../../src/features/admin/UserScreen";

export default function AdminUser() {
  const { userId } = useLocalSearchParams<{ userId: string }>();
  return <UserScreen userId={userId} />;
}
