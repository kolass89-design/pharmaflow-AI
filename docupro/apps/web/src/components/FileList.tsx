import { ArrowDown, ArrowUp, X } from "lucide-react";
import { FileKindIcon } from "./ToolIcon";
import { formatBytes, truncate } from "@/lib/format";

export function FileList({
  files,
  onRemove,
  onMove,
  reorderable = false,
  pages,
  disabled = false,
}: {
  files: File[];
  onRemove?: (index: number) => void;
  onMove?: (from: number, to: number) => void;
  reorderable?: boolean;
  pages?: (number | null)[];
  disabled?: boolean;
}) {
  if (!files.length) return null;
  const total = files.reduce((sum, file) => sum + file.size, 0);

  return (
    <div className="overflow-hidden rounded-xl border border-line bg-raised">
      <ul className="divide-y divide-line">
        {files.map((file, index) => (
          <li key={`${file.name}-${index}`} className="flex items-center gap-3 px-3 py-2.5">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-sunken text-muted">
              <FileKindIcon name={file.name} className="h-[17px] w-[17px]" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-medium text-content" title={file.name}>
                {truncate(file.name, 52)}
              </p>
              <p className="mt-0.5 text-[11px] text-muted">
                {formatBytes(file.size)}
                {pages?.[index] ? ` · ${pages[index]} pages` : ""}
              </p>
            </div>
            {reorderable && files.length > 1 && onMove && (
              <div className="flex items-center gap-0.5">
                <button
                  type="button"
                  className="icon-btn h-7 w-7"
                  onClick={() => onMove(index, index - 1)}
                  disabled={disabled || index === 0}
                  aria-label={`Move ${file.name} earlier`}
                >
                  <ArrowUp className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className="icon-btn h-7 w-7"
                  onClick={() => onMove(index, index + 1)}
                  disabled={disabled || index === files.length - 1}
                  aria-label={`Move ${file.name} later`}
                >
                  <ArrowDown className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              </div>
            )}
            {onRemove && (
              <button
                type="button"
                className="icon-btn h-7 w-7 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/50 dark:hover:text-red-400"
                onClick={() => onRemove(index)}
                disabled={disabled}
                aria-label={`Remove ${file.name}`}
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            )}
          </li>
        ))}
      </ul>
      {files.length > 1 && (
        <div className="flex items-center justify-between border-t border-line bg-sunken/60 px-3 py-2 text-[11.5px] text-muted">
          <span>
            {files.length} files · {formatBytes(total)}
          </span>
          {reorderable && <span>Use the arrows to set the order</span>}
        </div>
      )}
    </div>
  );
}
