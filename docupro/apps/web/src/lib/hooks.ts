/** Data hooks: catalog, capabilities, job polling, theme and media queries. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ApiError,
  type Capabilities,
  type Catalog,
  type Job,
  cancelJob as cancelJobRequest,
  fetchCapabilities,
  fetchCatalog,
  getJob,
} from "./api";
import { readJson, writeJson } from "./storage";

const CATALOG_KEY = "catalog.v1";

export function useCatalog() {
  const cached = useMemo(() => readJson<Catalog | null>(CATALOG_KEY, null), []);
  const [catalog, setCatalog] = useState<Catalog | null>(cached);
  const [loading, setLoading] = useState(!cached);
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchCatalog();
      setCatalog(data);
      writeJson(CATALOG_KEY, data);
      setError(null);
    } catch (caught) {
      setError(caught as ApiError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return { catalog, loading, error, refresh: load };
}

export function useCapabilities() {
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchCapabilities(controller.signal)
      .then(setCapabilities)
      .catch((caught) => {
        if ((caught as Error).name !== "AbortError") setError(caught as ApiError);
      });
    return () => controller.abort();
  }, []);
  return { capabilities, error };
}

const TERMINAL = new Set(["succeeded", "failed", "cancelled", "expired"]);

export function useJob(jobId: string | null, options?: { onSettled?: (job: Job) => void }) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [polling, setPolling] = useState(false);
  const settledRef = useRef<string | null>(null);
  const onSettledRef = useRef(options?.onSettled);
  onSettledRef.current = options?.onSettled;

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }
    let active = true;
    let timer: number | undefined;
    const controller = new AbortController();
    settledRef.current = null;
    setPolling(true);

    const tick = async () => {
      try {
        const current = await getJob(jobId, controller.signal);
        if (!active) return;
        setJob(current);
        setError(null);
        if (TERMINAL.has(current.status)) {
          setPolling(false);
          if (settledRef.current !== jobId) {
            settledRef.current = jobId;
            onSettledRef.current?.(current);
          }
          return;
        }
        timer = window.setTimeout(tick, current.status === "queued" ? 1200 : 900);
      } catch (caught) {
        if (!active) return;
        if ((caught as Error).name === "AbortError") return;
        setError(caught as ApiError);
        setPolling(false);
      }
    };

    void tick();
    return () => {
      active = false;
      controller.abort();
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId]);

  const cancel = useCallback(async () => {
    if (!jobId) return;
    try {
      const cancelled = await cancelJobRequest(jobId);
      setJob(cancelled);
    } catch (caught) {
      setError(caught as ApiError);
    }
  }, [jobId]);

  return { job, error, polling, cancel };
}

export type ThemePreference = "light" | "dark" | "system";

function applyTheme(preference: ThemePreference) {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = preference === "dark" || (preference === "system" && prefersDark);
  document.documentElement.classList.toggle("dark", dark);
  const meta = document.querySelector('meta[name="theme-color"]:not([media])');
  if (meta) meta.setAttribute("content", dark ? "#0b0f16" : "#ffffff");
}

type ThemeListener = (preference: ThemePreference) => void;
const themeListeners = new Set<ThemeListener>();

function readStoredTheme(): ThemePreference {
  try {
    const stored = localStorage.getItem("docupro.theme");
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

let currentTheme: ThemePreference = readStoredTheme();

function commitTheme(preference: ThemePreference) {
  currentTheme = preference;
  applyTheme(preference);
  try {
    if (preference === "system") localStorage.removeItem("docupro.theme");
    else localStorage.setItem("docupro.theme", preference);
  } catch {
    /* storage disabled */
  }
  themeListeners.forEach((listener) => listener(preference));
}

export function useTheme() {
  const [preference, setPreferenceState] = useState<ThemePreference>(currentTheme);

  useEffect(() => {
    const listener: ThemeListener = (value) => setPreferenceState(value);
    themeListeners.add(listener);
    // Sync in case another surface changed the theme before this one mounted.
    setPreferenceState(currentTheme);
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onMediaChange = () => {
      if (currentTheme === "system") applyTheme("system");
    };
    media.addEventListener("change", onMediaChange);
    return () => {
      themeListeners.delete(listener);
      media.removeEventListener("change", onMediaChange);
    };
  }, []);

  const setPreference = useCallback((value: ThemePreference) => {
    commitTheme(value);
  }, []);

  return { preference, setPreference };
}

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia(query).matches : false,
  );
  useEffect(() => {
    const media = window.matchMedia(query);
    const listener = (event: MediaQueryListEvent) => setMatches(event.matches);
    setMatches(media.matches);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, [query]);
  return matches;
}
