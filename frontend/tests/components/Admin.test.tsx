import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import type { ReactNode } from "react";

import { ApiError } from "../../src/api/errors";
import { AdminGate } from "../../src/features/admin/AdminGate";
import {
  blockUser,
  getOverview,
  getSettings,
  getUser,
  listAudit,
  listDocuments,
  retryDocument,
  updateSettings,
  type AdminUser,
} from "../../src/features/admin/api";
import { AuditScreen } from "../../src/features/admin/AuditScreen";
import { DocumentsScreen } from "../../src/features/admin/DocumentsScreen";
import { OverviewScreen } from "../../src/features/admin/OverviewScreen";
import { SettingsScreen } from "../../src/features/admin/SettingsScreen";
import { UserScreen } from "../../src/features/admin/UserScreen";
import { useAuthStore } from "../../src/features/auth/useAuthStore";
import i18n from "../../src/i18n";

jest.mock("../../src/features/admin/api", () => ({
  getOverview: jest.fn(),
  listUsers: jest.fn(),
  getUser: jest.fn(),
  blockUser: jest.fn(),
  unblockUser: jest.fn(),
  signOutUser: jest.fn(),
  setUserQuota: jest.fn(),
  deleteUser: jest.fn(),
  listDocuments: jest.fn(),
  retryDocument: jest.fn(),
  getSettings: jest.fn(),
  updateSettings: jest.fn(),
  listAudit: jest.fn(),
}));
jest.mock("expo-router", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  Redirect: () => null,
}));

const NOW = "2026-11-16T00:00:00Z";
const mocked = <T extends (...args: never[]) => unknown>(fn: T) =>
  fn as unknown as jest.MockedFunction<T>;

function wrap(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

function adminUser(overrides: Partial<AdminUser> = {}): AdminUser {
  return {
    id: "u2",
    email: "learner@example.com",
    role: "user",
    status: "active",
    sign_in_methods: ["email"],
    email_verified: true,
    created_at: NOW,
    document_count: 3,
    questions_today: 4,
    quota_override: null,
    ...overrides,
  };
}

beforeEach(async () => {
  jest.clearAllMocks();
  await i18n.changeLanguage("vi");
});

it("keeps non-admins and phones out", () => {
  useAuthStore.setState({
    status: "signedIn",
    user: {
      id: "u1",
      email: "a@b.c",
      email_verified: true,
      locale: "vi",
      role: "user",
      created_at: NOW,
    },
  });
  render(
    <AdminGate>
      <></>
    </AdminGate>,
  );
  // Tests run as a native platform, so the web-only notice comes first.
  expect(
    screen.getByText("Trang quản trị chỉ dùng trên trình duyệt web."),
  ).toBeTruthy();
});

it("shows the overview and highlights problems", async () => {
  mocked(getOverview).mockResolvedValue({
    users_total: 12,
    users_active_today: 5,
    documents_by_status: { READY: 7, FAILED: 1 },
    questions_today: 40,
    ai_calls_today: 90,
    ai_failures_today: 2,
    ai_tokens_today: 123456,
    ai_daily_token_budget: 0,
    ai_budget_used_percent: null,
    ai_enabled: false,
    circuit_state: "open",
    queue_length: 3,
  });
  wrap(<OverviewScreen />);

  expect(await screen.findByText("12")).toBeTruthy();
  expect(screen.getByText("Đang tắt")).toBeTruthy();
  expect(screen.getByText("Đang ngắt")).toBeTruthy();
  expect(screen.getByText("Lỗi")).toBeTruthy();
});

it("blocks a user only with a reason", async () => {
  mocked(getUser).mockResolvedValue(adminUser());
  mocked(blockUser).mockResolvedValue(adminUser({ status: "blocked" }));
  wrap(<UserScreen userId="u2" />);

  fireEvent.press(await screen.findByTestId("admin-block"));
  expect(
    screen.getByTestId("admin-confirm-ok").props.accessibilityState.disabled,
  ).toBe(true);
  fireEvent.changeText(screen.getByTestId("admin-reason"), "Spam");
  fireEvent.press(screen.getByTestId("admin-confirm-ok"));

  await waitFor(() => expect(blockUser).toHaveBeenCalledWith("u2", "Spam"));
  expect(screen.getByText(/không xem được nội dung tài liệu/)).toBeTruthy();
});

it("explains that admins cannot act on themselves", async () => {
  mocked(getUser).mockResolvedValue(adminUser());
  mocked(blockUser).mockRejectedValue(
    new ApiError("CANNOT_TARGET_SELF", "x", 409),
  );
  wrap(<UserScreen userId="u2" />);

  fireEvent.press(await screen.findByTestId("admin-block"));
  fireEvent.changeText(screen.getByTestId("admin-reason"), "x");
  fireEvent.press(screen.getByTestId("admin-confirm-ok"));
  expect(await screen.findByText(/chính tài khoản của bạn/)).toBeTruthy();
});

it("shows old and new values before saving settings", async () => {
  const values = {
    user_daily_query_limit: 30,
    max_file_size_mb: 20,
    max_pages: 200,
    max_documents_per_user: 10,
    ai_enabled: true,
    ai_daily_token_budget: 0,
  };
  mocked(getSettings).mockResolvedValue({ values, defaults: values });
  mocked(updateSettings).mockResolvedValue({ values, defaults: values });
  wrap(<SettingsScreen />);

  fireEvent.changeText(
    await screen.findByTestId("admin-setting-user_daily_query_limit"),
    "50",
  );
  fireEvent.press(screen.getByTestId("admin-ai-switch"));

  expect(screen.getByText("Câu hỏi mỗi người mỗi ngày: 30 → 50")).toBeTruthy();
  expect(screen.getByText("Tính năng AI: true → false")).toBeTruthy();
  fireEvent.press(screen.getByTestId("admin-settings-save"));
  await waitFor(() =>
    expect(updateSettings).toHaveBeenCalledWith({
      user_daily_query_limit: 50,
      ai_enabled: false,
    }),
  );
});

it("retries a failed document", async () => {
  mocked(listDocuments).mockResolvedValue({
    items: [
      {
        id: "d1",
        owner_id: "u2",
        owner_email: "learner@example.com",
        filename: "Bad.pdf",
        file_kind: "pdf",
        text_source: null,
        page_count: 3,
        status: "FAILED",
        error_code: "PROCESSING_FAILED",
        created_at: NOW,
        updated_at: NOW,
        last_job: {
          status: "failed",
          attempts: 3,
          last_error_code: "StorageError",
        },
      },
    ],
  });
  mocked(retryDocument).mockResolvedValue({} as never);
  wrap(<DocumentsScreen />);

  fireEvent.press(await screen.findByTestId("admin-retry-d1"));
  await waitFor(() => expect(retryDocument).toHaveBeenCalledWith("d1"));
});

it("lists audit entries with reasons", async () => {
  mocked(listAudit).mockResolvedValue({
    items: [
      {
        id: "a1",
        actor_email: "admin@example.com",
        action: "user.block",
        target_type: "user",
        target_id: "u2",
        before: { status: "active" },
        after: { status: "blocked" },
        reason: "Spam",
        created_at: NOW,
      },
    ],
  });
  wrap(<AuditScreen />);
  expect(await screen.findByText("Lý do: Spam")).toBeTruthy();
});
