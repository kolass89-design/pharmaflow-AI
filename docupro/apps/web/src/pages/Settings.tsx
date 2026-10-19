import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2,
  Download,
  HardDrive,
  RefreshCw,
  Server,
  ShieldCheck,
  Trash2,
  Wifi,
  WifiOff,
} from "lucide-react";
import { checkHealth, getApiBase, setApiBase } from "@/lib/api";
import { useCapabilities, useTheme, type ThemePreference } from "@/lib/hooks";
import { DEFAULT_SETTINGS, loadSettings, saveSettings, type AppSettings } from "@/lib/settings";
import { clearHistory, historyCount } from "@/lib/history";
import { removeKey, storageEstimate } from "@/lib/storage";
import { formatBytes } from "@/lib/format";
import { useToast } from "@/components/Toast";

const THEMES: { value: ThemePreference; title: string; description: string }[] = [
  { value: "light", title: "Light", description: "Bright surfaces, high contrast" },
  { value: "dark", title: "Dark", description: "Easy on the eyes at night" },
  { value: "system", title: "System", description: "Follow the operating system" },
];

export function SettingsPage() {
  const { preference, setPreference } = useTheme();
  const { capabilities } = useCapabilities();
  const { push } = useToast();
  const [settings, setSettings] = useState<AppSettings>(() => loadSettings());
  const [serviceUrl, setServiceUrl] = useState(() => getApiBase());
  const [checking, setChecking] = useState(false);
  const [health, setHealth] = useState<{ ok: boolean; version?: string; message?: string } | null>(null);
  const [installPrompt, setInstallPrompt] = useState<{ prompt: () => Promise<void> } | null>(null);
  const [online, setOnline] = useState(() => navigator.onLine);

  useEffect(() => {
    const handler = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event as unknown as { prompt: () => Promise<void> });
    };
    window.addEventListener("beforeinstallprompt", handler);
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("beforeinstallprompt", handler);
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  const update = (patch: Partial<AppSettings>) => {
    const next = { ...settings, ...patch };
    setSettings(next);
    saveSettings(next);
  };

  const testService = async () => {
    setChecking(true);
    const result = await checkHealth(serviceUrl);
    setHealth(result);
    setChecking(false);
    if (result.ok) push(`Connected to DOCUPRO ${result.version ?? ""}`.trim(), "success");
    else push(result.message ?? "The service did not respond.", "error");
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="text-[1.6rem] font-semibold tracking-tight text-content sm:text-[1.85rem]">Settings</h1>
        <p className="mt-1.5 text-[13px] text-muted">
          Preferences stay in this browser. Nothing here is sent to the conversion server.
        </p>
      </header>

      <section className="card p-5" aria-labelledby="appearance">
        <h2 id="appearance" className="text-[13.5px] font-semibold text-content">
          Appearance
        </h2>
        <p className="mt-0.5 text-[12px] text-muted">Choose a theme, or follow your device setting.</p>
        <div className="mt-3 grid gap-2 sm:grid-cols-3">
          {THEMES.map((theme) => {
            const active = preference === theme.value;
            return (
              <button
                key={theme.value}
                type="button"
                onClick={() => setPreference(theme.value)}
                aria-pressed={active}
                className={`rounded-xl border p-3 text-left transition-colors ${
                  active
                    ? "border-brand-400 bg-brand-50/60 dark:border-brand-700 dark:bg-brand-950/30"
                    : "border-line bg-surface hover:border-brand-200 dark:hover:border-brand-900"
                }`}
              >
                <span className="flex items-center justify-between">
                  <span className="text-[12.5px] font-semibold text-content">{theme.title}</span>
                  {active && <CheckCircle2 className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />}
                </span>
                <span className="mt-0.5 block text-[11px] text-muted">{theme.description}</span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="card p-5" aria-labelledby="conversions">
        <h2 id="conversions" className="text-[13.5px] font-semibold text-content">
          Conversion defaults
        </h2>
        <div className="mt-3 space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <label htmlFor="default-dpi" className="text-[12.5px] font-medium text-content">
                Default image resolution
              </label>
              <p className="text-[11.5px] text-muted">Applied to new conversions that render pages as images.</p>
            </div>
            <select
              id="default-dpi"
              className="input !w-auto min-w-[9rem]"
              value={settings.defaultDpi}
              onChange={(event) => update({ defaultDpi: Number(event.target.value) })}
            >
              {[96, 150, 200, 300].map((dpi) => (
                <option key={dpi} value={dpi}>
                  {dpi} DPI
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-start justify-between gap-4 border-t border-line pt-4">
            <div>
              <p className="text-[12.5px] font-medium text-content">Save local history</p>
              <p className="mt-0.5 text-[11.5px] leading-relaxed text-muted">
                Stores tool names, file names, sizes and outcomes in this browser only. Turn it off for shared
                computers.
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={settings.historyEnabled}
              aria-label="Save local history"
              onClick={() => update({ historyEnabled: !settings.historyEnabled })}
              className={`relative mt-0.5 inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
                settings.historyEnabled ? "bg-brand-600" : "bg-line"
              }`}
            >
              <span
                className={`inline-block h-[18px] w-[18px] transform rounded-full bg-white shadow transition-transform ${
                  settings.historyEnabled ? "translate-x-[23px]" : "translate-x-[3px]"
                }`}
              />
            </button>
          </div>

          <div className="flex flex-col gap-2 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-[11.5px] text-muted">
              {historyCount()} entries stored · {formatBytes(storageEstimate())} of local data used
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                className="btn-ghost !px-2.5 !py-1.5 text-[11.5px]"
                onClick={() => {
                  clearHistory();
                  push("Local history cleared.", "success");
                }}
              >
                <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                Clear history
              </button>
              <button
                type="button"
                className="btn-secondary !px-2.5 !py-1.5 text-[11.5px]"
                onClick={() => {
                  update(DEFAULT_SETTINGS);
                  setPreference("system");
                  push("Defaults restored.", "success");
                }}
              >
                <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
                Restore defaults
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="card p-5" aria-labelledby="service">
        <h2 id="service" className="flex items-center gap-1.5 text-[13.5px] font-semibold text-content">
          <Server className="h-4 w-4 text-muted" aria-hidden="true" />
          Conversion service
        </h2>
        <p className="mt-0.5 text-[12px] leading-relaxed text-muted">
          The web app uses this origin. The Windows and Android builds point at a hosted service; you can also
          override it here.
        </p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <input
            className="input"
            value={serviceUrl}
            placeholder="Same origin (recommended)"
            aria-label="Conversion service URL"
            onChange={(event) => setServiceUrl(event.target.value)}
          />
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-secondary !py-2 text-xs"
              onClick={testService}
              disabled={checking}
            >
              {checking ? "Testing…" : "Test"}
            </button>
            <button
              type="button"
              className="btn-primary !py-2 text-xs"
              onClick={() => {
                setApiBase(serviceUrl);
                push("Service URL saved.", "success");
                setHealth(null);
              }}
            >
              Save
            </button>
          </div>
        </div>
        {health && (
          <p
            className={`mt-2 flex items-center gap-1.5 text-[11.5px] ${
              health.ok ? "text-emerald-700 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
            }`}
          >
            {health.ok ? (
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              <WifiOff className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {health.ok ? `Connected · DOCUPRO ${health.version}` : health.message}
          </p>
        )}
        <div className="mt-3 grid gap-2 text-[11.5px] text-muted sm:grid-cols-2">
          <p className="flex items-center gap-1.5">
            {online ? (
              <Wifi className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            ) : (
              <WifiOff className="h-3.5 w-3.5 text-amber-600" aria-hidden="true" />
            )}
            {online ? "Online" : "Offline — interface cached, conversions need a connection"}
          </p>
          <p className="flex items-center gap-1.5">
            <HardDrive className="h-3.5 w-3.5" aria-hidden="true" />
            Retention: {capabilities?.limits.retentionMinutes ?? 30} min · max{" "}
            {capabilities ? formatBytes(capabilities.limits.maxUploadBytes) : "—"} per file
          </p>
        </div>
      </section>

      <section className="card p-5" aria-labelledby="install">
        <h2 id="install" className="text-[13.5px] font-semibold text-content">
          Install the app
        </h2>
        <p className="mt-0.5 text-[12px] leading-relaxed text-muted">
          Install DOCUPRO as a Progressive Web App for a full-screen window, an app icon and offline access to the
          interface. Windows and Android installers are produced by the release pipeline.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            className="btn-primary !py-2 text-xs"
            onClick={async () => {
              if (installPrompt) {
                await installPrompt.prompt();
                setInstallPrompt(null);
              } else {
                push("Use your browser menu → “Install app” or “Add to Home screen”.", "info");
              }
            }}
          >
            <Download className="h-3.5 w-3.5" aria-hidden="true" />
            Install DOCUPRO
          </button>
          <Link to="/about" className="btn-secondary !py-2 text-xs">
            Build information
          </Link>
        </div>
      </section>

      <section className="card p-5" aria-labelledby="data">
        <h2 id="data" className="flex items-center gap-1.5 text-[13.5px] font-semibold text-content">
          <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          Local data
        </h2>
        <p className="mt-1 text-[12px] leading-relaxed text-muted">
          DOCUPRO stores your theme, preferences, a cached tool list and (optionally) history. Clearing local data
          does not delete files on the server — use “Delete files now” on a result, or wait for automatic expiry.
        </p>
        <button
          type="button"
          className="btn-danger mt-3 !py-2 text-xs"
          onClick={() => {
            removeKey("catalog.v1");
            removeKey("history.v1");
            removeKey("settings.v1");
            setSettings(DEFAULT_SETTINGS);
            push("Local data cleared. Reload to fetch a fresh tool list.", "success");
          }}
        >
          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
          Clear cached data
        </button>
      </section>

      <p className="text-center text-[11px] text-muted">
        DOCUPRO {capabilities?.version ?? "1.0.0"} · engine: {capabilities?.engines.pdf ?? "MuPDF"} ·{" "}
        {capabilities?.engines.libreoffice ? "LibreOffice available" : "built-in Word renderer"}
      </p>
    </div>
  );
}
