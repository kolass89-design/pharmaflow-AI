import { CircleAlert, RefreshCw } from "lucide-react";
import type { ApiError } from "@/lib/api";

const HINTS: Record<string, string> = {
  password_required: "Open the PDF with its password first, or use the Unlock PDF tool.",
  invalid_password: "Check the password and try again. Passwords are case sensitive.",
  too_many_pages: "Split the document into smaller parts and convert them separately.",
  unsupported_input: "Choose a file whose format matches this tool.",
  invalid_file: "The file appears to be damaged or does not match its extension.",
  file_too_large: "Reduce the file size or raise the server limit if you administer it.",
  conversion_timeout: "Try a smaller file, a lower resolution, or fewer pages.",
  rate_limited: "Too many requests in a short time. Wait a moment before trying again.",
  queue_full: "The server is busy. Your request was not started — try again shortly.",
  ocr_unavailable: "OCR is not enabled on this server.",
  no_text: "No text was found. Try a clearer scan or enable OCR fallback.",
  no_tables: "No ruled tables were detected. Try PDF to Word or PDF to text instead.",
  already_searchable: "Every page already has a text layer, so no OCR was needed.",
  not_encrypted: "This PDF has no password, so there is nothing to unlock.",
  tool_unavailable: "This tool is not enabled on this server.",
  network_error: "Check that the conversion service is running and reachable.",
};

export function ErrorPanel({
  error,
  onRetry,
  onReset,
  retryLabel = "Try again",
}: {
  error: ApiError | string;
  onRetry?: () => void;
  onReset?: () => void;
  retryLabel?: string;
}) {
  const message = typeof error === "string" ? error : error.message;
  const code = typeof error === "string" ? undefined : error.code;
  const hint = code ? HINTS[code] : undefined;

  return (
    <div
      className="rounded-2xl border border-red-200 bg-red-50/80 p-5 dark:border-red-900/60 dark:bg-red-950/30"
      role="alert"
    >
      <div className="flex items-start gap-3">
        <CircleAlert className="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-400" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-red-900 dark:text-red-100">Conversion could not be completed</p>
          <p className="mt-1 text-[13px] leading-relaxed text-red-800/90 dark:text-red-200/90">{message}</p>
          {hint && <p className="mt-2 text-[12px] leading-relaxed text-red-700/80 dark:text-red-300/70">{hint}</p>}
          {code && (
            <p className="mt-2 font-mono text-[10.5px] uppercase tracking-wide text-red-700/60 dark:text-red-300/50">
              {code}
            </p>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            {onRetry && (
              <button type="button" className="btn-secondary !py-2 text-xs" onClick={onRetry}>
                <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
                {retryLabel}
              </button>
            )}
            {onReset && (
              <button type="button" className="btn-ghost !py-2 text-xs" onClick={onReset}>
                Start over
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
