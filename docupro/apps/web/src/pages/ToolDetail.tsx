import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ChevronRight,
  CircleHelp,
  Clock3,
  Info,
  Loader2,
  Lock,
  Play,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { ApiError, createJob, type Job, type Tool, type ToolOption } from "@/lib/api";
import { useCapabilities, useCatalog, useJob } from "@/lib/hooks";
import { addHistory } from "@/lib/history";
import { loadSettings } from "@/lib/settings";
import { takePendingFiles } from "@/lib/pending";
import { Dropzone } from "@/components/Dropzone";
import { FileList } from "@/components/FileList";
import { OptionField } from "@/components/OptionField";
import { ProgressPanel } from "@/components/ProgressPanel";
import { ResultList } from "@/components/ResultList";
import { ErrorPanel } from "@/components/ErrorPanel";
import { ToolIcon } from "@/components/ToolIcon";
import { useToast } from "@/components/Toast";
import { formatBytes, formatDuration } from "@/lib/format";

type Value = string | number | boolean;
type Stage = "idle" | "uploading" | "converting" | "done" | "failed";

function defaultOptions(tool: Tool, defaultDpi: number): Record<string, Value> {
  const values: Record<string, Value> = {};
  for (const option of tool.options) {
    const base = option.default;
    if (option.key === "dpi" && typeof base === "number") {
      values[option.key] = defaultDpi;
    } else if (base === null || base === undefined) {
      values[option.key] = option.type === "boolean" ? false : option.type === "number" ? (option.minimum ?? 0) : "";
    } else {
      values[option.key] = base as Value;
    }
  }
  return values;
}

export function ToolDetailPage() {
  const { toolId = "" } = useParams();
  const { catalog, loading, error: catalogError } = useCatalog();
  const { capabilities } = useCapabilities();
  const { push } = useToast();
  const settings = useMemo(() => loadSettings(), []);
  const tool = catalog?.tools.find((item) => item.id === toolId);

  const [files, setFiles] = useState<File[]>([]);
  const [options, setOptions] = useState<Record<string, Value>>({});
  const [stage, setStage] = useState<Stage>("idle");
  const [uploadPercent, setUploadPercent] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<ApiError | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const uploadRef = useRef<AbortController | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const adoptedRef = useRef(false);

  const maxUploadBytes = capabilities?.limits.maxUploadBytes;

  useEffect(() => {
    // Route change to another tool: drop any results from the previous one.
    setFiles([]);
    setJobId(null);
    setStage("idle");
    setSubmitError(null);
    setLocalError(null);
    setUploadPercent(0);
  }, [toolId]);

  useEffect(() => {
    if (!tool) return;
    setOptions(defaultOptions(tool, settings.defaultDpi));
    if (!adoptedRef.current) {
      adoptedRef.current = true;
      const pending = takePendingFiles();
      if (pending?.length) {
        const allowed = new Set(tool.input.extensions);
        const compatible = pending.filter((file) =>
          allowed.has(file.name.split(".").pop()?.toLowerCase() ?? ""),
        );
        if (compatible.length) {
          setFiles(compatible.slice(0, tool.maxFiles));
          if (compatible.length < pending.length) {
            push(
              `${pending.length - compatible.length} file(s) were skipped because this tool does not accept them.`,
              "info",
            );
          }
        } else if (pending.length) {
          push(`This tool does not accept ${pending[0].name.split(".").pop()?.toUpperCase()} files.`, "error");
        }
      }
    }
  }, [tool, settings.defaultDpi, push]);

  const handleSettled = useCallback(
    (job: Job) => {
      if (job.status === "succeeded") {
        setStage("done");
        addHistory({
          toolId: job.tool,
          toolTitle: tool?.title ?? job.tool,
          status: "succeeded",
          files: job.inputs.map((input) => ({ name: input.name, size: input.size })),
          artifacts: job.artifacts.map((artifact) => ({
            name: artifact.name,
            size: artifact.size,
            mediaType: artifact.mediaType,
            url: artifact.url,
          })),
          jobId: job.id,
          expiresAt: job.expiresAt,
        });
        push("Conversion complete — your file is ready.", "success");
        window.setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
      } else if (job.status === "failed") {
        setStage("failed");
        setSubmitError(
          new ApiError(job.error?.message ?? "The conversion failed.", job.error?.code ?? "conversion_failed"),
        );
        addHistory({
          toolId: job.tool,
          toolTitle: tool?.title ?? job.tool,
          status: "failed",
          files: job.inputs.map((input) => ({ name: input.name, size: input.size })),
          artifacts: [],
          jobId: job.id,
          error: job.error?.message,
        });
      } else if (job.status === "cancelled") {
        setStage("idle");
        setJobId(null);
        push("Conversion cancelled. Nothing was kept on the server.", "info");
      }
    },
    [push, tool],
  );

  const { job, error: jobError, cancel } = useJob(jobId, { onSettled: handleSettled });

  useEffect(() => {
    if (jobError && jobError.status !== 404) {
      setStage("failed");
      setSubmitError(jobError);
    }
  }, [jobError]);

  const acceptFiles = (incoming: File[]) => {
    if (!tool) return;
    setLocalError(null);
    setFiles((current) => {
      const merged = [...current, ...incoming];
      if (merged.length > tool.maxFiles) {
        setLocalError(
          `“${tool.title}” accepts ${tool.maxFiles === 1 ? "one file" : `${tool.maxFiles} files`} per conversion.`,
        );
        return merged.slice(0, tool.maxFiles);
      }
      return merged;
    });
    setStage("idle");
  };

  const removeFile = (index: number) => setFiles((current) => current.filter((_, position) => position !== index));

  const moveFile = (from: number, to: number) => {
    setFiles((current) => {
      if (to < 0 || to >= current.length) return current;
      const next = [...current];
      const [item] = next.splice(from, 1);
      next.splice(to, 0, item);
      return next;
    });
  };

  const setOption = (option: ToolOption, value: Value) => {
    setOptions((current) => ({ ...current, [option.key]: value }));
  };

  const validate = (): string | null => {
    if (!tool) return "Unknown tool.";
    if (files.length < tool.minFiles) {
      return tool.minFiles === 1 ? "Choose a file first." : `Choose at least ${tool.minFiles} files.`;
    }
    for (const option of tool.options) {
      if (option.required && String(options[option.key] ?? "").trim() === "") {
        return `“${option.label}” is required.`;
      }
    }
    return null;
  };

  const submit = async () => {
    if (!tool) return;
    const problem = validate();
    if (problem) {
      setLocalError(problem);
      return;
    }
    setLocalError(null);
    setSubmitError(null);
    setUploadPercent(0);
    setStage("uploading");
    const controller = new AbortController();
    uploadRef.current = controller;
    try {
      const created = await createJob({
        tool: tool.id,
        files,
        options,
        onUploadProgress: setUploadPercent,
        signal: controller.signal,
      });
      setJobId(created.id);
      setStage("converting");
    } catch (caught) {
      const error = caught as ApiError;
      if (error.code === "cancelled") {
        setStage("idle");
        return;
      }
      setSubmitError(error);
      setStage("failed");
    } finally {
      uploadRef.current = null;
    }
  };

  const cancelRun = async () => {
    setCancelling(true);
    try {
      if (stage === "uploading") {
        uploadRef.current?.abort();
      } else {
        await cancel();
      }
      setStage("idle");
      setJobId(null);
      push("Conversion cancelled. Nothing was kept on the server.", "info");
    } finally {
      setCancelling(false);
    }
  };

  const reset = () => {
    setFiles([]);
    setJobId(null);
    setStage("idle");
    setSubmitError(null);
    setLocalError(null);
    setUploadPercent(0);
    if (tool) setOptions(defaultOptions(tool, settings.defaultDpi));
  };

  if (loading && !catalog) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-5 w-40" />
        <div className="skeleton h-9 w-72" />
        <div className="skeleton h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (!tool) {
    return (
      <div className="card mx-auto max-w-md p-8 text-center">
        <CircleHelp className="mx-auto h-8 w-8 text-muted" aria-hidden="true" />
        <h1 className="mt-3 text-base font-semibold text-content">This tool does not exist</h1>
        <p className="mt-1 text-[12.5px] text-muted">
          {catalogError?.message ?? "The link may be outdated, or the tool was removed."}
        </p>
        <Link to="/tools" className="btn-primary mt-5 !py-2 text-xs">
          Browse all tools
        </Link>
      </div>
    );
  }

  const primaryOptions = tool.options.filter((option) => !option.advanced);
  const advancedOptions = tool.options.filter((option) => option.advanced);
  const busy = stage === "uploading" || stage === "converting";
  const totalSize = files.reduce((sum, file) => sum + file.size, 0);

  return (
    <div className="space-y-6">
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[12px] text-muted">
        <Link to="/tools" className="inline-flex items-center gap-1 hover:text-content">
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          All tools
        </Link>
        <ChevronRight className="h-3 w-3 opacity-50" aria-hidden="true" />
        <span className="text-content">{tool.title}</span>
      </nav>

      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3.5">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-brand-100 bg-brand-50 text-brand-700 dark:border-brand-900/50 dark:bg-brand-950/40 dark:text-brand-300">
            <ToolIcon toolId={tool.id} className="h-[22px] w-[22px]" />
          </span>
          <div>
            <h1 className="text-[1.45rem] font-semibold tracking-tight text-content sm:text-[1.7rem]">
              {tool.title}
            </h1>
            <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-muted">{tool.description}</p>
            <div className="mt-2.5 flex flex-wrap items-center gap-2 text-[11px] text-muted">
              <span className="rounded-full border border-line bg-raised px-2 py-0.5">{tool.engine}</span>
              <span className="rounded-full border border-line bg-raised px-2 py-0.5">
                → {tool.outputLabel}
              </span>
              <span className="rounded-full border border-line bg-raised px-2 py-0.5">
                ~{formatDuration(tool.estimatedSeconds)}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          {stage === "done" && job ? (
            <div ref={resultRef}>
              <ResultList job={job} onReset={reset} onDeleted={reset} />
            </div>
          ) : busy ? (
            <ProgressPanel
              stage={stage}
              uploadPercent={uploadPercent}
              job={job}
              onCancel={cancelRun}
              cancelling={cancelling}
            />
          ) : (
            <div className="card p-4 sm:p-5">
              <Dropzone
                accept={tool.input.extensions}
                multiple={tool.maxFiles > 1}
                maxFiles={tool.maxFiles}
                onFiles={acceptFiles}
                maxUploadBytes={maxUploadBytes}
                compact={files.length > 0}
                label={files.length ? "Add another file or drag it here" : "Choose a file or drag it here"}
                hint={`${tool.input.extensions.map((ext) => ext.toUpperCase()).join(" · ")}${
                  maxUploadBytes ? ` · up to ${formatBytes(maxUploadBytes)}` : ""
                }`}
              />
              {files.length > 0 && (
                <div className="mt-4 space-y-3">
                  <FileList
                    files={files}
                    onRemove={removeFile}
                    onMove={moveFile}
                    reorderable={tool.maxFiles > 1}
                    disabled={busy}
                  />
                  {tool.maxFiles > 1 && (
                    <p className="text-[11px] text-muted">
                      {files.length} of {tool.maxFiles} allowed · {formatBytes(totalSize)} total
                    </p>
                  )}
                </div>
              )}

              {tool.options.length > 0 && (
                <div className="mt-5 border-t border-line pt-4">
                  <h2 className="text-[13px] font-semibold text-content">Options</h2>
                  <div className="mt-3 grid gap-4 sm:grid-cols-2">
                    {primaryOptions.map((option) => (
                      <div
                        key={option.key}
                        className={
                          option.type === "pages" || option.type === "password" ? "sm:col-span-2" : ""
                        }
                      >
                        <OptionField
                          option={option}
                          value={options[option.key] ?? ""}
                          onChange={(value) => setOption(option, value)}
                        />
                      </div>
                    ))}
                  </div>
                  {advancedOptions.length > 0 && (
                    <div className="mt-3">
                      <button
                        type="button"
                        className="flex items-center gap-1.5 text-[12px] font-medium text-muted hover:text-content"
                        onClick={() => setShowAdvanced((current) => !current)}
                        aria-expanded={showAdvanced}
                      >
                        <ChevronRight
                          className={`h-3.5 w-3.5 transition-transform ${showAdvanced ? "rotate-90" : ""}`}
                          aria-hidden="true"
                        />
                        Advanced options ({advancedOptions.length})
                      </button>
                      {showAdvanced && (
                        <div className="mt-3 grid gap-4 rounded-xl border border-line bg-sunken/40 p-4 sm:grid-cols-2">
                          {advancedOptions.map((option) => (
                            <div key={option.key}>
                              <OptionField
                                option={option}
                                value={options[option.key] ?? ""}
                                onChange={(value) => setOption(option, value)}
                              />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {localError && (
                <p className="mt-4 text-[12.5px] font-medium text-amber-700 dark:text-amber-400" role="alert">
                  {localError}
                </p>
              )}

              <div className="mt-5 flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="flex items-center gap-1.5 text-[11px] text-muted">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                  Processed on your conversion server · deleted automatically
                </p>
                <button
                  type="button"
                  className="btn-primary w-full sm:w-auto"
                  onClick={submit}
                  disabled={!files.length || !tool.available}
                >
                  <Play className="h-4 w-4" aria-hidden="true" />
                  Convert now
                </button>
              </div>
            </div>
          )}

          {stage === "failed" && submitError && (
            <ErrorPanel
              error={submitError}
              onRetry={() => {
                setSubmitError(null);
                setJobId(null);
                void submit();
              }}
              onReset={reset}
            />
          )}

          {!tool.available && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-[12.5px] text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-100">
              <p className="font-semibold">This tool is not enabled on this server</p>
              <p className="mt-1">{tool.unavailableReason ?? "The required conversion engine is missing."}</p>
              <p className="mt-1 opacity-80">
                Administrators can enable it by installing the engine — see the deployment guide.
              </p>
            </div>
          )}
        </div>

        <aside className="space-y-4">
          <div className="card p-4">
            <h2 className="flex items-center gap-1.5 text-[12.5px] font-semibold text-content">
              <Info className="h-3.5 w-3.5 text-muted" aria-hidden="true" />
              Input & output
            </h2>
            <dl className="mt-3 space-y-2.5 text-[12px]">
              <div className="flex items-start justify-between gap-3">
                <dt className="text-muted">Accepted</dt>
                <dd className="text-right font-medium text-content">
                  {tool.input.extensions.map((ext) => ext.toUpperCase()).join(", ")}
                </dd>
              </div>
              <div className="flex items-start justify-between gap-3">
                <dt className="text-muted">Produces</dt>
                <dd className="text-right font-medium text-content">{tool.outputLabel}</dd>
              </div>
              <div className="flex items-start justify-between gap-3">
                <dt className="text-muted">Files per job</dt>
                <dd className="text-right font-medium text-content">
                  {tool.minFiles === tool.maxFiles
                    ? tool.maxFiles
                    : `${tool.minFiles}–${tool.maxFiles}`}
                </dd>
              </div>
              <div className="flex items-start justify-between gap-3">
                <dt className="text-muted">Typical time</dt>
                <dd className="flex items-center gap-1 text-right font-medium text-content">
                  <Clock3 className="h-3 w-3 text-muted" aria-hidden="true" />
                  {formatDuration(tool.estimatedSeconds)}
                </dd>
              </div>
            </dl>
          </div>

          {tool.limitations.length > 0 && (
            <div className="card p-4">
              <h2 className="text-[12.5px] font-semibold text-content">Known limitations</h2>
              <ul className="mt-2.5 space-y-2 text-[11.5px] leading-relaxed text-muted">
                {tool.limitations.map((limitation) => (
                  <li key={limitation} className="flex gap-2">
                    <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-muted/60" aria-hidden="true" />
                    {limitation}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="card p-4">
            <h2 className="flex items-center gap-1.5 text-[12.5px] font-semibold text-content">
              <Lock className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
              Privacy
            </h2>
            <ul className="mt-2.5 space-y-2 text-[11.5px] leading-relaxed text-muted">
              <li className="flex gap-2">
                <Trash2 className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
                Files are deleted after download or {capabilities?.limits.retentionMinutes ?? 30} minutes.
              </li>
              <li className="flex gap-2">
                <Lock className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
                Download links are random and token protected.
              </li>
              <li className="flex gap-2">
                <ShieldCheck className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
                No account, no tracking, no training on your documents.
              </li>
            </ul>
            <Link
              to="/privacy"
              className="mt-3 inline-flex items-center gap-1 text-[11.5px] font-medium text-brand-700 hover:underline dark:text-brand-300"
            >
              Privacy details
              <ChevronRight className="h-3 w-3" aria-hidden="true" />
            </Link>
          </div>
        </aside>
      </div>

      {busy && (
        <p className="flex items-center justify-center gap-2 text-[11.5px] text-muted" aria-live="polite">
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          You can safely leave this page — the conversion continues, but the link is only shown here.
        </p>
      )}
    </div>
  );
}
