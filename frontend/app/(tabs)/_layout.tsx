import { Tabs } from "expo-router";

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#007AFF",
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Thư viện",
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: "Hỏi đáp",
        }}
      />
      <Tabs.Screen
        name="study"
        options={{
          title: "Ôn tập",
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Hồ sơ",
        }}
      />
    </Tabs>
  );
}
