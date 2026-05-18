"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { resolveBase } from "@/lib/api";

interface AppConfig {
  app_name: string;
  logo_url: string;
  background_url: string;
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
      _cachedConfig = { app_name: "DeepTutor", logo_url: "/logo-ver2.png", background_url: "" };
      _fetchPromise = null;
      return _cachedConfig;
    });

  return _fetchPromise;
}

export function AppConfigProvider({
  children,
  initialAppName,
  initialLogoUrl,
  initialBackgroundUrl,
}: {
  children: React.ReactNode;
  initialAppName?: string;
  initialLogoUrl?: string;
  initialBackgroundUrl?: string;
}) {
  const [config, setConfig] = useState<AppConfig>({
    app_name: initialAppName ?? "DeepTutor",
    logo_url: initialLogoUrl ?? "/logo-ver2.png",
    background_url: initialBackgroundUrl ?? "",
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
  return ctx ?? { app_name: "DeepTutor", logo_url: "/logo-ver2.png", background_url: "" };
}
