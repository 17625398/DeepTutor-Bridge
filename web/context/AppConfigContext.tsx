"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { resolveBase } from "@/lib/api";

interface AppConfig {
  app_name: string;
}

const AppConfigContext = createContext<AppConfig | null>(null);

let _cachedConfig: AppConfig | null = null;
let _fetchPromise: Promise<AppConfig> | null = null;

async function fetchAppConfig(): Promise<AppConfig> {
  if (_cachedConfig) return _cachedConfig;
  if (_fetchPromise) return _fetchPromise;

  _fetchPromise = fetch(`${resolveBase()}/api/v1/config/app`)
    .then((res) => res.json())
    .then((data) => {
      _cachedConfig = data;
      _fetchPromise = null;
      return data;
    })
    .catch(() => {
      _cachedConfig = { app_name: "DeepTutor" };
      _fetchPromise = null;
      return _cachedConfig;
    });

  return _fetchPromise;
}

export function AppConfigProvider({
  children,
  initialAppName,
}: {
  children: React.ReactNode;
  initialAppName?: string;
}) {
  const [config, setConfig] = useState<AppConfig>({
    app_name: initialAppName ?? "DeepTutor",
  });

  useEffect(() => {
    fetchAppConfig().then(setConfig);
  }, []);

  return (
    <AppConfigContext.Provider value={config}>
      {children}
    </AppConfigContext.Provider>
  );
}

export function useAppConfig(): AppConfig {
  const ctx = useContext(AppConfigContext);
  return ctx ?? { app_name: "DeepTutor" };
}
