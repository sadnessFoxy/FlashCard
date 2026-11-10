import en from "../../src/i18n/locales/en.json";
import vi from "../../src/i18n/locales/vi.json";

function keys(obj: Record<string, unknown>, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    v !== null && typeof v === "object"
      ? keys(v as Record<string, unknown>, `${prefix}${k}.`)
      : [`${prefix}${k}`],
  );
}

it("vi and en have the same keys (nothing untranslated)", () => {
  expect(keys(en).sort()).toEqual(keys(vi).sort());
});
