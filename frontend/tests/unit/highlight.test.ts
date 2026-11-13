import { isHighlighted } from "../../src/features/documents/highlight";

const snippet =
  "Đạo hàm là hệ số góc của tiếp tuyến. Nó đo tốc độ thay đổi của hàm số tại một điểm…";

it("marks a paragraph contained in the snippet, despite spacing", () => {
  expect(isHighlighted("Đạo hàm là hệ số góc\ncủa  tiếp tuyến.", snippet)).toBe(
    true,
  );
});

it("marks a paragraph in which the snippet starts", () => {
  expect(
    isHighlighted(
      "Mở đầu. Đạo hàm là hệ số góc của tiếp tuyến. Nó đo tốc độ thay đổi.",
      "Đạo hàm là hệ số góc của tiếp tuyến. Nó đo tốc độ",
    ),
  ).toBe(true);
});

it("leaves unrelated paragraphs alone", () => {
  expect(isHighlighted("Tích phân là diện tích dưới đồ thị.", snippet)).toBe(
    false,
  );
  expect(isHighlighted("", snippet)).toBe(false);
});
