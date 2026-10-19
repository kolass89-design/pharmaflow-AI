import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CircleAlert,
  CircleCheck,
  Clock3,
  Download,
  History,
  Loader2,
  Trash2,
} from "lucide-react";
import { saveArtifact } from "@/lib/api";
import { clearHistory, historyCount, listHistory, removeHistory, type HistoryEntry } from "@/lib/history";
import { loadSettings } from "@/lib/settings";
import { formatBytes, formatRelative } from "@/lib/format";
import { Modal } from "@/components/Modal";
import { useToast } from "@/components/Toast";
import { ToolIcon } from "@/components/ToolIcon";

export function RecentPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>(() => listHistory());
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const { push } = useToast();
  const enabled = useMemo(() => loadSettings().historyEnabled, []);

  useEffect(() => {
    const refresh = () => setEntries(listHistory());
    window.addEventListener("docupro:history", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("docupro:history", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  const download = async (artifact: HistoryEntry["artifacts"][number]) => {
    setBusy(artifact.url);
    try {
      await saveArtifact(artifact.url, artifact.name);
      push(`Downloaded ${artifact.name}`, "success");
    } catch {
      push("This file has expired and was deleted from the server.", "error");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-[1.6rem] font-semibold tracking-tight text-content sm:text-[1.85rem]">
            Recent conversions
          </h1>
          <p className="mt-1.5 max-w-2xl text-[13px] leading-relaxed text-muted">
            Stored only in this browser. Names, sizes and outcomes are kept locally — document contents never are.
          </p>
        </div>
        {entries.length > 0 && (
          <button type="button" className="btn-danger !py-2 text-xs" onClick={() => setConfirming(true)}>
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
            Clear history
          </button>
        )}
      </header>

      {!enabled && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-[12.5px] text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-100">
          History is turned off. New conversions will not be recorded in this browser.{" "}
          <Link to="/settings" className="font-medium underline">
            Enable history
          </Link>
        </div>
      )}

      {entries.length === 0 ? (
        <div className="card flex flex-col items-center px-6 py-16 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sunken text-muted">
            <History className="h-5 w-5" aria-hidden="true" />
          </span>
          <h2 className="mt-3 text-sm font-semibold text-content">No conversions yet</h2>
          <p className="mt-1 max-w-sm text-[12.5px] leading-relaxed text-muted">
            Once you convert a document, it appears here with a shortcut back to the tool. Files on the server
            still expire automatically.
          </p>
          <Link to="/tools" className="btn-primary mt-5 !py-2 text-xs">
            Start a conversion
            <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        </div>
      ) : (
        <ul className="space-y-2.5">
          {entries.map((entry) => {
            const expired = entry.expiresAt ? entry.expiresAt * 1000 < Date.now() : false;
            return (
              <li key={entry.id} className="card p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex min-w-0 items-start gap-3">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sunken text-muted">
                      <ToolIcon toolId={entry.toolId} className="h-[18px] w-[18px]" />
                    </span>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-[13.5px] font-semibold text-content">{entry.toolTitle}</h2>
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
                            entry.status === "succeeded"
                              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"
                              : "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300"
                          }`}
                        >
                          {entry.status === "succeeded" ? (
                            <CircleCheck className="h-3 w-3" aria-hidden="true" />
                          ) : (
                            <CircleAlert className="h-3 w-3" aria-hidden="true" />
                          )}
                          {entry.status === "succeeded" ? "Completed" : "Failed"}
                        </span>
                      </div>
                      <p className="mt-1 truncate text-[11.5px] text-muted" title={entry.files.map((f) => f.name).join(", ")}>
                        {entry.files.map((file) => `${file.name} (${formatBytes(file.size)})`).join(" · ")}
                      </p>
                      {entry.error && <p className="mt-1 text-[11.5px] text-red-600 dark:text-red-400">{entry.error}</p>}
                      <p className="mt-1 flex items-center gap-1.5 text-[10.5px] text-muted/80">
                        <Clock3 className="h-3 w-3" aria-hidden="true" />
                        {formatRelative(entry.createdAt)}
                        {entry.artifacts.length > 0 && (expired ? " · files expired" : " · files may still be available")}
                      </p>
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-wrap items-center gap-1.5">
                    {entry.artifacts.map((artifact) => (
                      <button
                        key={artifact.url}
                        type="button"
                        className="btn-secondary !px-2.5 !py-1.5 text-[11.5px]"
                        onClick={() => download(artifact)}
                        disabled={busy === artifact.url || expired}
                        title={expired ? "Expired" : `Download ${artifact.name}`}
                      >
                        {busy === artifact.url ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                        ) : (
                          <Download className="h-3.5 w-3.5" aria-hidden="true" />
                        )}
                        {artifact.name.length > 22 ? `${artifact.name.slice(0, 20)}…` : artifact.name}
                      </button>
                    ))}
                    <Link to={`/tool/${entry.toolId}`} className="btn-ghost !px-2.5 !py-1.5 text-[11.5px]">
                      Use again
                    </Link>
                    <button
                      type="button"
                      className="icon-btn h-8 w-8"
                      onClick={() => removeHistory(entry.id)}
                      aria-label="Remove this entry"
                    >
                      <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <Modal open={confirming} onClose={() => setConfirming(false)} title="Clear conversion history?">
        <p className="text-[13px] leading-relaxed text-muted">
          This removes {historyCount()} entries from this browser. Files already deleted from the server stay
          deleted; files still available can be downloaded until they expire.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" className="btn-secondary !py-2 text-xs" onClick={() => setConfirming(false)}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-danger !py-2 text-xs"
            onClick={() => {
              clearHistory();
              setConfirming(false);
              push("Local history cleared.", "success");
            }}
          >
            Clear history
          </button>
        </div>
      </Modal>
    </div>
  );
}
