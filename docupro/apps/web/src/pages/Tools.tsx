import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { useCatalog } from "@/lib/hooks";
import { ToolCard } from "@/components/ToolCard";
import { peekPendingFiles, takePendingFiles } from "@/lib/pending";
import { formatBytes } from "@/lib/format";

const CATEGORY_TABS = [
  { id: "all", label: "All tools" },
  { id: "pdf", label: "PDF" },
  { id: "word", label: "Word" },
  { id: "image", label: "Images" },
  { id: "other", label: "Other formats" },
];

export function ToolsPage() {
  const { catalog, loading, error } = useCatalog();
  const [params, setParams] = useSearchParams();
  const category = params.get("category") ?? "all";
  const [query, setQuery] = useState(params.get("q") ?? "");
  const [picked, setPicked] = useState<File[] | null>(null);

  useEffect(() => {
    const files = peekPendingFiles();
    if (files?.length) setPicked(files);
  }, []);

  useEffect(() => {
    const next = new URLSearchParams(params);
    if (query.trim()) next.set("q", query.trim());
    else next.delete("q");
    if (next.toString() !== params.toString()) setParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  const tools = catalog?.tools ?? [];
  const pickedExtensions = useMemo(
    () => new Set((picked ?? []).map((file) => file.name.split(".").pop()?.toLowerCase() ?? "")),
    [picked],
  );

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return tools
      .filter((tool) => (category === "all" ? true : tool.category === category))
      .filter((tool) => {
        if (!term) return true;
        return (
          tool.title.toLowerCase().includes(term) ||
          tool.subtitle.toLowerCase().includes(term) ||
          tool.description.toLowerCase().includes(term) ||
          tool.keywords.some((keyword) => keyword.includes(term)) ||
          tool.input.extensions.some((ext) => ext.includes(term))
        );
      })
      .sort((a, b) => {
        const aMatch = a.input.extensions.some((ext) => pickedExtensions.has(ext)) ? 0 : 1;
        const bMatch = b.input.extensions.some((ext) => pickedExtensions.has(ext)) ? 0 : 1;
        if (aMatch !== bMatch) return aMatch - bMatch;
        if (a.available !== b.available) return a.available ? -1 : 1;
        return a.title.localeCompare(b.title);
      });
  }, [tools, category, query, pickedExtensions]);

  const changeCategory = (id: string) => {
    const next = new URLSearchParams(params);
    if (id === "all") next.delete("category");
    else next.set("category", id);
    setParams(next, { replace: true });
  };

  const clearPicked = () => {
    takePendingFiles();
    setPicked(null);
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-[1.6rem] font-semibold tracking-tight text-content sm:text-[1.85rem]">
          {category === "all"
            ? "All tools"
            : (CATEGORY_TABS.find((tab) => tab.id === category)?.label ?? "Tools")}
        </h1>
        <p className="mt-1.5 max-w-2xl text-[13.5px] leading-relaxed text-muted">
          {catalog?.categories.find((item) => item.id === category)?.description ??
            "Every conversion available on your conversion server, with honest limits stated up front."}
        </p>
      </header>

      {picked && picked.length > 0 && (
        <div className="flex flex-col gap-2 rounded-xl border border-brand-200 bg-brand-50/60 px-4 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-brand-900/60 dark:bg-brand-950/30">
          <p className="text-[12.5px] text-brand-900 dark:text-brand-100">
            <span className="font-semibold">
              {picked.length} file{picked.length === 1 ? "" : "s"} selected
            </span>{" "}
            ({picked.map((file) => file.name).join(", ")} · {formatBytes(picked.reduce((sum, f) => sum + f.size, 0))}
            ). Tools that accept them are shown first.
          </p>
          <button type="button" className="btn-ghost !px-2 !py-1 text-[11.5px]" onClick={clearPicked}>
            <X className="h-3.5 w-3.5" aria-hidden="true" />
            Clear selection
          </button>
        </div>
      )}

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative max-w-md flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
            aria-hidden="true"
          />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search a conversion, format or keyword…"
            aria-label="Search tools"
            className="input pl-9"
          />
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <SlidersHorizontal className="mr-1 hidden h-3.5 w-3.5 text-muted sm:block" aria-hidden="true" />
          {CATEGORY_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => changeCategory(tab.id)}
              aria-pressed={category === tab.id}
              className={`chip ${category === tab.id ? "chip-active" : ""}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-[13px] text-red-800 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-200">
          The tool catalog could not be loaded: {error.message}
        </div>
      )}

      {loading && !tools.length ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, index) => (
            <div key={index} className="card h-[172px] p-5">
              <div className="skeleton h-10 w-10 rounded-xl" />
              <div className="skeleton mt-4 h-3.5 w-2/3" />
              <div className="skeleton mt-2.5 h-3 w-1/2" />
              <div className="skeleton mt-3 h-3 w-full" />
            </div>
          ))}
        </div>
      ) : filtered.length ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((tool) => (
            <ToolCard key={tool.id} tool={tool} />
          ))}
        </div>
      ) : (
        <div className="card flex flex-col items-center px-6 py-14 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sunken text-muted">
            <Search className="h-5 w-5" aria-hidden="true" />
          </span>
          <h2 className="mt-3 text-sm font-semibold text-content">No tools match this search</h2>
          <p className="mt-1 max-w-sm text-[12.5px] text-muted">
            Try a different keyword, or clear the filters to see all {tools.length} conversions.
          </p>
          <button
            type="button"
            className="btn-secondary mt-4 !py-2 text-xs"
            onClick={() => {
              setQuery("");
              changeCategory("all");
            }}
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}
