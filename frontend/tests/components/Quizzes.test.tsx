import AsyncStorage from "@react-native-async-storage/async-storage";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import type { ReactNode } from "react";

import { ApiError } from "../../src/api/errors";
import { listDocuments } from "../../src/features/documents/api";
import {
  createQuiz,
  getQuiz,
  listQuizzes,
  submitAttempt,
  type AttemptResult,
  type QuizDetail,
} from "../../src/features/quizzes/api";
import { CreateQuizScreen } from "../../src/features/quizzes/CreateQuizScreen";
import { QuizzesTab } from "../../src/features/quizzes/QuizzesTab";
import { TakeQuizScreen } from "../../src/features/quizzes/TakeQuizScreen";
import i18n from "../../src/i18n";

jest.mock("../../src/features/quizzes/api", () => ({
  listQuizzes: jest.fn(),
  getQuiz: jest.fn(),
  createQuiz: jest.fn(),
  deleteQuiz: jest.fn(),
  submitAttempt: jest.fn(),
}));
jest.mock("../../src/features/documents/api", () => ({
  listDocuments: jest.fn(),
}));
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockBack = jest.fn();
jest.mock("expo-router", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: mockBack,
    canGoBack: () => true,
  }),
}));

const list = listQuizzes as jest.MockedFunction<typeof listQuizzes>;
const get = getQuiz as jest.MockedFunction<typeof getQuiz>;
const create = createQuiz as jest.MockedFunction<typeof createQuiz>;
const submit = submitAttempt as jest.MockedFunction<typeof submitAttempt>;
const docs = listDocuments as jest.MockedFunction<typeof listDocuments>;

const NOW = "2026-11-14T00:00:00Z";
const quiz: QuizDetail = {
  id: "q1",
  space_id: "s1",
  title: "Giải tích.pdf",
  page_start: 2,
  page_end: 3,
  question_count: 2,
  attempt_count: 0,
  last_score: null,
  created_at: NOW,
  questions: [
    {
      id: "a",
      position: 0,
      prompt: "Đạo hàm là gì?",
      options: ["Hệ số góc", "Diện tích", "Giới hạn", "Ma trận"],
    },
    {
      id: "b",
      position: 1,
      prompt: "Tích phân là gì?",
      options: ["Hệ số góc", "Diện tích", "Giới hạn", "Ma trận"],
    },
  ],
};

const result: AttemptResult = {
  id: "t1",
  quiz_id: "q1",
  score: 1,
  total: 2,
  created_at: NOW,
  results: [
    {
      question_id: "a",
      prompt: "Đạo hàm là gì?",
      options: quiz.questions[0]!.options,
      choice: 0,
      correct_index: 0,
      is_correct: true,
      explanation: "Theo định nghĩa.",
      source: { document_id: "d1", document_name: "Giải tích.pdf", page: 2 },
    },
    {
      question_id: "b",
      prompt: "Tích phân là gì?",
      options: quiz.questions[1]!.options,
      choice: null,
      correct_index: 1,
      is_correct: false,
      explanation: "Tích phân xác định là diện tích.",
      source: { document_id: "d1", document_name: "Giải tích.pdf", page: 3 },
    },
  ],
};

function wrap(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

beforeEach(async () => {
  jest.clearAllMocks();
  await AsyncStorage.clear();
  await i18n.changeLanguage("vi");
  docs.mockResolvedValue({
    items: [
      {
        id: "d1",
        space_id: "s1",
        filename: "Giải tích.pdf",
        file_kind: "pdf",
        size_bytes: 1,
        page_count: 3,
        status: "READY",
        error_code: null,
        created_at: NOW,
        updated_at: NOW,
      },
    ],
    total_documents: 1,
    max_documents: 10,
  });
});

it("lists quizzes with their pages and last score", async () => {
  list.mockResolvedValue({
    items: [{ ...quiz, attempt_count: 1, last_score: 1 }],
  });
  wrap(<QuizzesTab spaceId="s1" />);
  expect(
    await screen.findByText("trang 2–3 · 2 câu · lần gần nhất 1/2"),
  ).toBeTruthy();
});

it("creates a quiz from a page range and opens it", async () => {
  create.mockResolvedValue(quiz);
  wrap(<CreateQuizScreen spaceId="s1" />);

  fireEvent.changeText(await screen.findByTestId("quiz-page-from"), "2");
  fireEvent.changeText(screen.getByTestId("quiz-page-to"), "3");
  fireEvent.press(screen.getByTestId("quiz-generate"));

  await waitFor(() =>
    expect(create).toHaveBeenCalledWith({
      space_id: "s1",
      document_id: "d1",
      page_start: 2,
      page_end: 3,
      question_count: 10,
    }),
  );
  expect(mockReplace).toHaveBeenCalledWith({
    pathname: "/spaces/quizzes/[quizId]",
    params: { quizId: "q1" },
  });
});

it("explains when the quiz quota is used up", async () => {
  create.mockRejectedValue(new ApiError("USER_QUOTA_EXCEEDED", "x", 429));
  wrap(<CreateQuizScreen spaceId="s1" />);
  await screen.findByTestId("quiz-doc-d1");
  fireEvent.press(screen.getByTestId("quiz-generate"));
  expect(await screen.findByText(/hết lượt tạo trắc nghiệm/)).toBeTruthy();
});

it("answers, submits and reviews wrong answers with their source", async () => {
  get.mockResolvedValue(quiz);
  submit.mockResolvedValue(result);
  wrap(<TakeQuizScreen quizId="q1" />);

  expect(await screen.findByText("Câu 1/2")).toBeTruthy();
  fireEvent.press(screen.getByTestId("quiz-option-0"));
  fireEvent.press(screen.getByTestId("quiz-next"));
  expect(screen.getByText(/1 câu chưa trả lời/)).toBeTruthy();
  fireEvent.press(screen.getByTestId("quiz-submit"));

  await waitFor(() =>
    expect(submit).toHaveBeenCalledWith("q1", [
      { question_id: "a", choice: 0 },
      { question_id: "b", choice: null },
    ]),
  );
  expect(await screen.findByText("1/2 câu đúng")).toBeTruthy();
  expect(screen.getByText("Đáp án đúng: B. Diện tích")).toBeTruthy();
  expect(screen.getByText("Bạn chọn: bỏ trống")).toBeTruthy();
  fireEvent.press(screen.getByText("Giải tích.pdf · trang 3"));
  expect(mockPush).toHaveBeenCalledWith({
    pathname: "/spaces/citation",
    params: {
      documentId: "d1",
      page: "3",
      highlight: "Tích phân xác định là diện tích.",
    },
  });
});

it("keeps unfinished answers when leaving, and resumes them", async () => {
  get.mockResolvedValue(quiz);
  const first = wrap(<TakeQuizScreen quizId="q1" />);

  fireEvent.press(await screen.findByTestId("quiz-option-2"));
  fireEvent.press(screen.getByTestId("quiz-back"));
  fireEvent.press(screen.getByTestId("quiz-leave-save"));
  await waitFor(() => expect(mockBack).toHaveBeenCalled());
  first.unmount();

  wrap(<TakeQuizScreen quizId="q1" />);
  expect(await screen.findByTestId("quiz-resumed")).toBeTruthy();
  expect(
    screen.getByTestId("quiz-option-2").props.accessibilityState.selected,
  ).toBe(true);
});
