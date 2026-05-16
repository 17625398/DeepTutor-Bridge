/* eslint-disable i18n/no-literal-ui-text */
"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch, apiUrl } from "@/lib/api";

type Integration = {
  name: string;
  ui?: {
    title?: string;
    entry?: { type?: "link" | "iframe"; url?: string };
    iframe?: { sandbox?: string };
    nav?: { open_in_new_tab?: boolean };
  };
};

export default function IntegrationPage() {
  const params = useParams<{ name: string }>();
  const name = params?.name;
  const [integration, setIntegration] = useState<Integration | null>(null);
  const [error, setError] = useState<string>("");
  const [probe, setProbe] = useState<
    | { ok: true; status_code?: number }
    | { ok: false; reason?: string; error?: string }
    | null
  >(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setError("");
      setIntegration(null);
      setProbe(null);
      try {
        const res = await apiFetch(apiUrl(`/api/v1/integrations/${name}`));
        if (!res.ok) {
          setError(`Failed to load integration: ${name}`);
          return;
        }
        const json = (await res.json()) as Integration;
        if (!cancelled) setIntegration(json);
      } catch {
        if (!cancelled) setError(`Failed to load integration: ${name}`);
      }
    }
    if (name) load();
    return () => {
      cancelled = true;
    };
  }, [name]);

  useEffect(() => {
    let cancelled = false;
    async function runProbe() {
      try {
        const res = await apiFetch(apiUrl(`/api/v1/integrations/${name}/probe`));
        if (!res.ok) return;
        const json = (await res.json()) as
          | { ok: true; status_code?: number }
          | { ok: false; reason?: string; error?: string };
        if (!cancelled) setProbe(json);
      } catch {
        if (!cancelled) setProbe({ ok: false, reason: "probe_failed" });
      }
    }
    if (integration && name) runProbe();
    return () => {
      cancelled = true;
    };
  }, [integration, name]);

  const title = useMemo(() => {
    return integration?.ui?.title || integration?.name || String(name || "");
  }, [integration, name]);

  const entryType = integration?.ui?.entry?.type || "link";
  const entryUrl = integration?.ui?.entry?.url || "";
  const sandbox = integration?.ui?.iframe?.sandbox || "allow-scripts allow-same-origin";
  const openInNewTab = integration?.ui?.nav?.open_in_new_tab !== false;

  const effectiveUrl = useMemo(() => {
    if (typeof window === "undefined") return entryUrl;
    if (!entryUrl) return "";
    try {
      if (entryUrl.startsWith("/")) {
        return `${window.location.origin}${entryUrl}`;
      }
      const url = new URL(entryUrl);
      const loopback = new Set(["localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"]);
      const clientHost = window.location.hostname;
      if (loopback.has(url.hostname) && !loopback.has(clientHost)) {
        url.hostname = clientHost;
        return url.toString();
      }
      return url.toString();
    } catch {
      return entryUrl;
    }
  }, [entryUrl]);

  if (error) {
    return (
      <div className="p-6 text-[var(--foreground)]">
        <div className="text-[16px] font-semibold">{title}</div>
        <div className="mt-2 text-[13px] text-[var(--muted-foreground)]">{error}</div>
      </div>
    );
  }

  if (!integration) {
    return (
      <div className="p-6 text-[var(--foreground)]">
        <div className="text-[16px] font-semibold">{String(name || "")}</div>
        <div className="mt-2 text-[13px] text-[var(--muted-foreground)]">
          Loading…
        </div>
      </div>
    );
  }

  if (entryType === "iframe" && entryUrl) {
    return (
      <div className="flex h-[calc(100vh-56px)] flex-col">
        <div className="px-6 pt-5 pb-3">
          <div className="text-[16px] font-semibold text-[var(--foreground)]">
            {title}
          </div>
          <div className="mt-1 text-[12px] text-[var(--muted-foreground)]">
            {effectiveUrl}
          </div>
        </div>
        <div className="flex-1 px-6 pb-6">
          <iframe
            src={effectiveUrl}
            className="h-full w-full rounded-xl border border-[var(--border)] bg-[var(--background)]"
            sandbox={sandbox}
            referrerPolicy="no-referrer"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 text-[var(--foreground)]">
      <div className="text-[16px] font-semibold">{title}</div>
      <div className="mt-2 text-[13px] text-[var(--muted-foreground)]">
        {effectiveUrl || "No URL configured for this integration."}
      </div>
      {probe && !probe.ok && (
        <div className="mt-2 text-[12px] text-[var(--muted-foreground)]">
          Unreachable: {probe.error || probe.reason || "unknown"}
        </div>
      )}
      {entryUrl && (
        <a
          href={effectiveUrl}
          target={openInNewTab ? "_blank" : undefined}
          rel={openInNewTab ? "noreferrer noopener" : undefined}
          className="mt-4 inline-flex rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-[13px] hover:bg-[var(--background)]/60"
        >
          Open
        </a>
      )}
    </div>
  );
}
