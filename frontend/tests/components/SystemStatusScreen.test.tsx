import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import type { ReactNode } from "react";

import i18n from "../../src/i18n";
import { NetworkError } from "../../src/api/errors";
import {
  getSystemStatus,
  type SystemStatus,
} from "../../src/features/system/api";
import { SystemStatusScreen } from "../../src/features/system/SystemStatusScreen";

// Mock the network layer: no backend or app config needed.
jest.mock("../../src/features/system/api", () => ({
  getSystemStatus: jest.fn(),
}));

const mockedGetSystemStatus = getSystemStatus as jest.MockedFunction<
  typeof getSystemStatus
>;

const ALL_UP: SystemStatus = {
  status: "ok",
  version: "1.0.0",
  checks: {
    database: {
      status: "up",
      latency_ms: 3.2,
      error_code: null,
      pgvector_version: "0.8.7",
    },
    redis: { status: "up", latency_ms: 0.8, error_code: null },
  },
};

function renderScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { gcTime: 0 } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return render(<SystemStatusScreen apiUrl="http://localhost:8000" />, {
    wrapper,
  });
}

beforeEach(async () => {
  mockedGetSystemStatus.mockReset();
  await i18n.changeLanguage("vi");
});

it("shows every service up when the backend reports ok", async () => {
  mockedGetSystemStatus.mockResolvedValue(ALL_UP);

  renderScreen();

  expect(await screen.findByText("Mọi thứ hoạt động bình thường")).toBeTruthy();
  expect(screen.getByText(/pgvector 0\.8\.7/)).toBeTruthy();
  expect(screen.getAllByText("Hoạt động")).toHaveLength(3);
});

it("points out the failing service when degraded", async () => {
  mockedGetSystemStatus.mockResolvedValue({
    ...ALL_UP,
    status: "degraded",
    checks: {
      ...ALL_UP.checks,
      redis: { status: "down", latency_ms: 2000, error_code: "TIMEOUT" },
    },
  });

  renderScreen();

  expect(await screen.findByText("Một số dịch vụ đang gặp sự cố")).toBeTruthy();
  expect(screen.getByText(/Quá thời gian chờ/)).toBeTruthy();
  expect(screen.getByText("Không hoạt động")).toBeTruthy();
});

it("reports an unreachable backend with the URL to check", async () => {
  mockedGetSystemStatus.mockRejectedValue(new NetworkError("offline"));

  renderScreen();

  expect(
    await screen.findByText("Không kết nối được tới backend"),
  ).toBeTruthy();
  expect(screen.getByText(/http:\/\/localhost:8000/)).toBeTruthy();
});

it("check-again button calls the API again", async () => {
  mockedGetSystemStatus.mockResolvedValue(ALL_UP);
  renderScreen();
  await screen.findByText("Mọi thứ hoạt động bình thường");

  fireEvent.press(screen.getByTestId("system-status-refresh"));

  await waitFor(() => expect(mockedGetSystemStatus).toHaveBeenCalledTimes(2));
});

it("renders English after switching language", async () => {
  await i18n.changeLanguage("en");
  mockedGetSystemStatus.mockResolvedValue(ALL_UP);

  renderScreen();

  expect(await screen.findByText("All systems operational")).toBeTruthy();
});
