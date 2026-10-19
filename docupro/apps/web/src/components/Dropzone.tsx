import { useCallback, useEffect, useRef, useState } from "react";
import { ClipboardPaste, UploadCloud } from "lucide-react";
import { formatBytes } from "@/lib/format";

interface DropzoneProps {
  accept: string[];
  multiple: boolean;
  maxFiles: number;
  onFiles: (files: File[]) => void;
  disabled?: boolean;
  compact?: boolean;
  maxUploadBytes?: number;
  label?: string;
  hint?: string;
}

/**
 * Accessible upload surface: click, keyboard, drag & drop and paste.
 * Client-side checks give instant feedback; the server remains the authority.
 */
export function Dropzone({
  accept,
  multiple,
  maxFiles,
  onFiles,
  disabled = false,
  compact = false,
  maxUploadBytes,
  label = "Choose a file or drag it here",
  hint,
}: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const dragDepth = useRef(0);

  const acceptAttr = accept.map((ext) => `.${ext}`).join(",");
  const acceptLabel = accept.map((ext) => ext.toUpperCase()).join(" · ");

  const validate = useCallback(
    (incoming: File[]): File[] => {
      setLocalError(null);
      if (!incoming.length) return [];
      const allowed = new Set(accept);
      const rejected: string[] = [];
      const tooBig: string[] = [];
      const valid = incoming.filter((file) => {
        const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
        if (!allowed.has(ext)) {
          rejected.push(file.name);
          return false;
        }
        if (maxUploadBytes && file.size > maxUploadBytes) {
          tooBig.push(file.name);
          return false;
        }
        return true;
      });
      if (rejected.length) {
        setLocalError(
          rejected.length === 1
            ? `“${rejected[0]}” is not an accepted format for this tool.`
            : `${rejected.length} files were skipped because their format is not accepted.`,
        );
      } else if (tooBig.length) {
        setLocalError(
          `“${tooBig[0]}” is larger than the ${formatBytes(maxUploadBytes)} limit.`,
        );
      }
      if (valid.length > maxFiles) {
        setLocalError(
          `This tool accepts ${maxFiles === 1 ? "one file" : `${maxFiles} files`} per conversion.`,
        );
      }
      return valid.slice(0, maxFiles);
    },
    [accept, maxFiles, maxUploadBytes],
  );

  const handleFiles = useCallback(
    (list: FileList | File[] | null) => {
      if (!list || disabled) return;
      const files = Array.from(list);
      const valid = validate(files);
      if (valid.length) onFiles(valid);
    },
    [disabled, onFiles, validate],
  );

  useEffect(() => {
    const onPaste = (event: ClipboardEvent) => {
      if (disabled) return;
      const files = Array.from(event.clipboardData?.files ?? []);
      if (files.length) {
        event.preventDefault();
        const target = event.target as HTMLElement | null;
        if (target && ["INPUT", "TEXTAREA"].includes(target.tagName)) return;
        handleFiles(files);
      }
    };
    document.addEventListener("paste", onPaste);
    return () => document.removeEventListener("paste", onPaste);
  }, [disabled, handleFiles]);

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-label={`${label}. Accepted formats: ${acceptLabel}.`}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(event) => {
          if (disabled) return;
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragEnter={(event) => {
          event.preventDefault();
          dragDepth.current += 1;
          if (!disabled) setDragging(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) event.dataTransfer.dropEffect = "copy";
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          dragDepth.current = Math.max(0, dragDepth.current - 1);
          if (dragDepth.current === 0) setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          dragDepth.current = 0;
          setDragging(false);
          handleFiles(event.dataTransfer.files);
        }}
        className={`group relative flex w-full cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed text-center transition-all duration-200 ${
          compact ? "gap-2 px-6 py-7" : "gap-3 px-6 py-12 sm:py-14"
        } ${
          disabled
            ? "cursor-not-allowed border-line bg-sunken/60 opacity-60"
            : dragging
              ? "border-brand-500 bg-brand-50/80 shadow-inner dark:bg-brand-950/30"
              : "border-line bg-raised hover:border-brand-300 hover:bg-brand-50/40 dark:hover:border-brand-800 dark:hover:bg-brand-950/20"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          className="sr-only"
          accept={acceptAttr}
          multiple={multiple}
          disabled={disabled}
          onChange={(event) => {
            handleFiles(event.target.files);
            event.target.value = "";
          }}
        />
        <span
          className={`flex items-center justify-center rounded-2xl transition-all duration-200 ${
            compact ? "h-10 w-10" : "h-14 w-14"
          } ${
            dragging
              ? "scale-105 bg-brand-600 text-white"
              : "bg-brand-50 text-brand-600 group-hover:bg-brand-100 dark:bg-brand-950/50 dark:text-brand-300"
          }`}
        >
          <UploadCloud className={compact ? "h-5 w-5" : "h-6 w-6"} strokeWidth={1.9} aria-hidden="true" />
        </span>
        <span className="block">
          <span className={`block font-semibold text-content ${compact ? "text-sm" : "text-[15px]"}`}>
            {label}
          </span>
          <span className="mt-1 block text-xs text-muted">
            {hint ?? `${acceptLabel}${maxUploadBytes ? ` · up to ${formatBytes(maxUploadBytes)}` : ""}`}
          </span>
        </span>
        {!compact && (
          <span className="mt-1 hidden items-center gap-1.5 text-[11px] text-muted/80 sm:flex">
            <ClipboardPaste className="h-3.5 w-3.5" aria-hidden="true" />
            You can also paste a file from the clipboard
          </span>
        )}
      </div>
      {localError && (
        <p className="mt-2 text-xs font-medium text-amber-700 dark:text-amber-400" role="alert">
          {localError}
        </p>
      )}
    </div>
  );
}
