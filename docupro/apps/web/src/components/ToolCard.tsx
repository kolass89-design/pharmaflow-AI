import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import type { Tool } from "@/lib/api";
import { ToolIcon } from "./ToolIcon";

export function ToolCard({ tool, compact = false }: { tool: Tool; compact?: boolean }) {
  const disabled = !tool.available;
  const body = (
    <>
      <div className="flex items-start justify-between gap-3">
        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${
            disabled
              ? "border-line bg-sunken text-muted"
              : "border-brand-100 bg-brand-50 text-brand-700 dark:border-brand-900/50 dark:bg-brand-950/40 dark:text-brand-300"
          }`}
        >
          <ToolIcon toolId={tool.id} className="h-[19px] w-[19px]" />
        </span>
        <ArrowUpRight
          className="h-4 w-4 shrink-0 text-muted/50 transition-all duration-200 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-brand-600 dark:group-hover:text-brand-300"
          aria-hidden="true"
        />
      </div>
      <div className={compact ? "mt-3" : "mt-4"}>
        <h3 className="text-[14.5px] font-semibold leading-tight text-content">{tool.title}</h3>
        <p className="mt-1 text-[12.5px] leading-relaxed text-muted">
          {disabled ? (tool.unavailableReason ?? "Unavailable on this server") : tool.subtitle}
        </p>
      </div>
      {!compact && !disabled && (
        <p className="mt-3 line-clamp-2 text-[12.5px] leading-relaxed text-muted/85">{tool.description}</p>
      )}
      {disabled && (
        <span className="mt-3 inline-flex rounded-full bg-amber-50 px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
          Unavailable
        </span>
      )}
    </>
  );

  if (disabled) {
    return (
      <div className="group block cursor-not-allowed rounded-2xl border border-dashed border-line bg-raised/50 p-4 opacity-80 sm:p-5">
        {body}
      </div>
    );
  }

  return (
    <Link
      to={`/tool/${tool.id}`}
      className="group block rounded-2xl border border-line bg-raised p-4 shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-lift focus-visible:-translate-y-0.5 sm:p-5 dark:hover:border-brand-800"
    >
      {body}
    </Link>
  );
}
