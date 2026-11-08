import en from "../../src/i18n/locales/en.json";
import vi from "../../src/i18n/locales/vi.json";

function keys(obj: Record<string, unknown>, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    v !== null && typeof v === "object"
      ? keys(v as Record<string, unknown>, `${prefix}${k}.`)
      : [`${prefix}${k}`],
  );
}

it("tiếng Việt và tiếng Anh có cùng bộ khóa (không còn chuỗi chưa dịch)", () => {
  expect(keys(en).sort()).toEqual(keys(vi).sort());
});
