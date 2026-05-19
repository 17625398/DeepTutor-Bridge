import { createInstance } from "i18next";

import enApp from "@/locales/en/app.json";
import zhApp from "@/locales/zh/app.json";

export type AppLanguage = "en" | "zh";

const resources = {
  en: { app: enApp },
  zh: { app: zhApp },
};

function normalizeLanguage(lang: unknown): AppLanguage {
  if (!lang) return "zh";
  const s = String(lang).toLowerCase();
  if (s === "zh" || s === "cn" || s === "chinese") return "zh";
  return "en";
}

export function getServerLanguage(): AppLanguage {
  return "zh";
}

const serverI18n = createInstance();
serverI18n.init({
  lng: getServerLanguage(),
  fallbackLng: "en",
  resources,
  defaultNS: "app",
  ns: ["app"],
  keySeparator: false,
  interpolation: {
    escapeValue: false,
  },
  returnEmptyString: false,
  returnNull: false,
});

export const serverT = serverI18n.t.bind(serverI18n);
