import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Clock3,
  Download,
  Eye,
  FileDown,
  Loader2,
  RefreshCw,
  Trash2,
} from "lucide-react";
import type { Job } from "@/lib/api";
import { deleteJob, fetchArtifact, saveArtifact } from "@/lib/api";
import { formatBytes, formatDateTime } from "@/lib/format";
import { Modal } from "./Modal";
import { useToast } from "./Toast";
import { FileKindIcon } from "./ToolIcon";

function useCountdown(expiresAt: number | null): string | null {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!expiresAt) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [expiresAt]);
  if (!expiresAt) return null;
  const remaining = Math.max(0, Math.floor(expiresAt * 1000 - now));
  const minutes = Math.floor(remaining / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function metaChips(meta: Record<string, unknown>): string[] {
  const chips: string[] = [];
  const pages = meta.pages ?? (meta.primaryMeta as Record<string, unknown> | undefined)?.pages;
  const files = meta.files;
  if (typeof pages === "number" && pages > 0) chips.push(`${pages} ${pages === 1 ? "page" : "pages"}`);
  if (typeof files === "number" && files > 1) chips.push(`${files} files`);
  const saved = (meta.primaryMeta as Record<string, unknown> | undefined)?.savedPercent ?? meta.savedPercent;
  if (typeof saved === "number" && saved > 0) chips.push(`${Math.round(saved)}% smaller`);
  const method = (meta.primaryMeta as Record<string, unknown> | undefined)?.method ?? meta.method;
  if (typeof method === "string") {
    const labels: Record<string, string> = {
      libreoffice: "LibreOffice rendering",
      "python-html": "Built-in renderer",
      layout: "Layout preserved",
      ocr: "OCR",
      "ocr-fallback": "OCR fallback",
      "html-layout": "HTML layout",
    };
    chips.push(labels[method] ?? method);
  }
  const confidence = (meta.primaryMeta as Record<string, unknown> | undefined)?.confidence;
  if (typeof confidence === "number" && confidence > 0) chips.push(`OCR ${Math.round(confidence * 100)}%`);
  return chips;
}

export function ResultList({
  job,
  onReset,
  onDeleted,
}: {
  job: Job;
  onReset: () => void;
  onDeleted: () => void;
}) {
  const { push } = useToast();
  const [busy, setBusy] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ name: string; type: string; url: string } | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const countdown = useCountdown(job.expiresAt);
  const chips = useMemo(() => metaChips(job.meta), [job.meta]);
  const primaryMeta = (job.meta?.primaryMeta as Record<string, unknown> | undefined) ?? {};

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview.url);
    };
  }, [preview]);

  const download = async (artifact: Job["artifacts"][number]) => {
    setBusy(artifact.id);
    try {
      await saveArtifact(artifact.url, artifact.name);
      push(`Downloaded ${artifact.name}`, "success");
    } catch (error) {
      push((error as Error).message || "The download failed. The file may have expired.", "error");
    } finally {
      setBusy(null);
    }
  };

  const openPreview = async (artifact: Job["artifacts"][number]) => {
    setPreviewing(true);
    try {
      const { blob } = await fetchArtifact(artifact.url);
      const url = URL.createObjectURL(blob);
      setPreview({ name: artifact.name, type: artifact.mediaType, url });
    } catch (error) {
      push((error as Error).message || "Preview unavailable.", "error");
    } finally {
      setPreviewing(false);
    }
  };

  const closePreview = () => {
    if (preview) URL.revokeObjectURL(preview.url);
    setPreview(null);
  };

  const deleteFiles = async () => {
    try {
      await deleteJob(job.id);
      push("Server copies deleted immediately.", "success");
      onDeleted();
    } catch {
      push("The files could not be deleted. They will expire automatically.", "error");
    }
  };

  const isImage = (type: string) => type.startsWith("image/");
  const isPdf = (type: string) => type === "application/pdf";
  const isText = (type: string) => type.startsWith("text/");

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5 dark:border-emerald-900/60 dark:bg-emerald-950/25">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-emerald-900 dark:text-emerald-100">Ready to download</p>
            <p className="mt-1 text-[12.5px] text-emerald-800/85 dark:text-emerald-200/80">
              {job.artifacts.length === 1
                ? job.artifacts[0].name
                : `${job.artifacts.length} files generated`}
              {job.finishedAt ? ` · finished ${formatDateTime(job.finishedAt)}` : ""}
            </p>
            {chips.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {chips.map((chip) => (
                  <span
                    key={chip}
                    className="rounded-full border border-emerald-200/80 bg-white/70 px-2 py-0.5 text-[10.5px] font-medium text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200"
                  >
                    {chip}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="card divide-y divide-line overflow-hidden">
        {job.artifacts.map((artifact) => {
          const previewable =
            isImage(artifact.mediaType) || isPdf(artifact.mediaType) || isText(artifact.mediaType);
          return (
            <div key={artifact.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sunken text-muted">
                  <FileKindIcon name={artifact.name} className="h-[18px] w-[18px]" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-[13.5px] font-medium text-content" title={artifact.name}>
                    {artifact.name}
                  </p>
                  <p className="mt-0.5 text-[11.5px] text-muted">
                    {formatBytes(artifact.size)} ·{" "}
                    {artifact.mediaType.split("/").pop()?.replace("openxmlformats-officedocument.", "")}
                  </p>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {previewable && (
                  <button
                    type="button"
                    className="btn-secondary !px-3 !py-1.5 text-xs"
                    onClick={() => openPreview(artifact)}
                    disabled={previewing}
                  >
                    {previewing ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                    ) : (
                      <Eye className="h-3.5 w-3.5" aria-hidden="true" />
                    )}
                    Preview
                  </button>
                )}
                <button
                  type="button"
                  className="btn-primary !px-3.5 !py-1.5 text-xs"
                  onClick={() => download(artifact)}
                  disabled={busy === artifact.id}
                >
                  {busy === artifact.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  ) : (
                    <Download className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                  Download
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {job.warnings.length > 0 && (
        <ul className="space-y-1.5 rounded-xl border border-amber-200 bg-amber-50/70 p-3.5 text-[12px] leading-relaxed text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-100">
          {job.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}

      <div className="flex flex-col gap-3 text-[11.5px] text-muted sm:flex-row sm:items-center sm:justify-between">
        <p className="flex items-center gap-1.5">
          <Clock3 className="h-3.5 w-3.5" aria-hidden="true" />
          {countdown
            ? `Server copies are deleted in ${countdown} (or immediately after download).`
            : "Server copies are deleted automatically."}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" className="btn-ghost !px-2.5 !py-1.5 text-[11.5px]" onClick={deleteFiles}>
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
            Delete files now
          </button>
          <button type="button" className="btn-secondary !px-3 !py-1.5 text-[11.5px]" onClick={onReset}>
            <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
            Convert another file
          </button>
        </div>
      </div>

      {primaryMeta.pages ? (
        <p className="flex items-center gap-1.5 text-[11px] text-muted/80">
          <FileDown className="h-3 w-3" aria-hidden="true" />
          Validated: the generated file was opened and checked before this link was shown.
        </p>
      ) : null}

      <Modal open={Boolean(preview)} onClose={closePreview} title={preview?.name ?? "Preview"} wide>
        {preview &&
          (preview.type.startsWith("image/") ? (
            <img src={preview.url} alt={preview.name} className="mx-auto max-h-[70vh] rounded-lg" />
          ) : preview.type === "application/pdf" ? (
            <iframe src={preview.url} title={preview.name} className="h-[70vh] w-full rounded-lg border border-line" />
          ) : (
            <pre className="max-h-[70vh] overflow-auto whitespace-pre-wrap rounded-lg bg-sunken p-4 text-[12.5px] leading-relaxed text-content">
              <TextPreview url={preview.url} />
            </pre>
          ))}
      </Modal>
    </div>
  );
}

function TextPreview({ url }: { url: string }) {
  const [text, setText] = useState("Loading preview…");
  useEffect(() => {
    let active = true;
    fetch(url)
      .then((response) => response.text())
      .then((value) => {
        if (active) setText(value.slice(0, 20_000));
      })
      .catch(() => {
        if (active) setText("Preview unavailable.");
      });
    return () => {
      active = false;
    };
  }, [url]);
  return <>{text}</>;
}
