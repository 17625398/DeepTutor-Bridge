"use client";

import { useAppConfig } from "@/context/AppConfigContext";

export function BackgroundImage() {
  const { background_url } = useAppConfig();

  if (!background_url) return null;

  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10"
      style={{
        backgroundImage: `url(${background_url})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    />
  );
}
