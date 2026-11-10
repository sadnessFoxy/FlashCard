import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { getLocales } from "expo-localization";

import vi from "./locales/vi.json";
import en from "./locales/en.json";

const resources = {
  vi: { translation: vi },
  en: { translation: en },
} as const;

// Device language, falling back to Vietnamese
const deviceLanguage = getLocales()[0]?.languageCode ?? "vi";
const supportedLanguages = Object.keys(resources);
const initialLanguage = supportedLanguages.includes(deviceLanguage)
  ? deviceLanguage
  : "vi";

void i18n.use(initReactI18next).init({
  resources,
  lng: initialLanguage,
  fallbackLng: "vi",
  defaultNS: "translation",
  interpolation: {
    escapeValue: false, // React escapes already
  },
  compatibilityJSON: "v4",
});

export default i18n;
export type SupportedLanguage = keyof typeof resources;
