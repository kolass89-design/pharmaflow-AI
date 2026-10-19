import { useEffect, useState } from "react";
import { Loader2, Square } from "lucide-react";
import type { Job } from "@/lib/api";

export function ProgressPanel({
  stage,
  uploadPercent,
  job,
  onCancel,
  cancelling,
}: {
  stage: "uploading" | "converting";
  uploadPercent: number;
  job: Job | null;
  onCancel: () => void;
  cancelling: boolean;
}) {
  const [elapsed, setElapsed] = useState(0);
  const startedAt = job?.startedAt ?? null;

  useEffect(() => {
    const started = startedAt ? startedAt * 1000 : Date.now();
    const timer = window.setInterval(() => setElapsed(Math.max(0, Math.round((Date.now() - started) / 1000))), 500);
    return () => window.clearInterval(timer);
  }, [startedAt]);

  const percent = stage === "uploading" ? uploadPercent : Math.round((job?.progress ?? 0) * 100);
  const message =
    stage === "uploading"
      ? uploadPercent >= 100
        ? "Upload complete, starting engine…"
        : "Uploading your file securely…"
      : (job?.message ?? "Preparing conversion…");

  return (
    <div className="card p-5 sm:p-6" aria-live="polite" aria-busy="true">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-300">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-content">
              {stage === "uploading" ? "Sending your document" : "Converting"}
            </p>
            <p className="mt-0.5 text-xs text-muted">{message}</p>
          </div>
        </div>
        <span className="text-sm font-semibold tabular-nums text-content">{percent}%</span>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-line/70">
        <div
          className="h-full rounded-full bg-brand-600 transition-[width] duration-500 ease-out"
          style={{ width: `${Math.max(3, percent)}%` }}
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Conversion progress"
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-[11.5px] text-muted">
          {elapsed > 0 ? `Elapsed ${elapsed}s` : "Just started"} · Files are deleted automatically after download
        </p>
        <button
          type="button"
          className="btn-ghost !px-3 !py-1.5 text-xs text-red-600 hover:bg-red-50 hover:text-red-700 dark:text-red-400 dark:hover:bg-red-950/40"
          onClick={onCancel}
          disabled={cancelling}
        >
          {cancelling ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          ) : (
            <Square className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          {cancelling ? "Cancelling…" : "Cancel"}
        </button>
      </div>
    </div>
  );
}
