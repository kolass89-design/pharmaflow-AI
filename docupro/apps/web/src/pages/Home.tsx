import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BadgeCheck,
  Clock3,
  FileSpreadsheet,
  FileText,
  FileType2,
  Image as ImageIcon,
  Lock,
  ShieldCheck,
  Sparkles,
  Trash2,
  Zap,
} from "lucide-react";
import { useCapabilities, useCatalog } from "@/lib/hooks";
import { setPendingFiles } from "@/lib/pending";
import { Dropzone } from "@/components/Dropzone";
import { ToolCard } from "@/components/ToolCard";
import { useToast } from "@/components/Toast";

const ALL_EXTENSIONS = [
  "pdf", "docx", "doc", "xlsx", "pptx", "csv", "txt", "html", "htm",
  "jpg", "jpeg", "png", "webp", "heic", "heif", "gif", "bmp", "tif", "tiff",
];

const CATEGORY_ART = [
  { id: "pdf", title: "PDF tools", icon: FileText, accent: "from-brand-500/10 to-brand-500/0" },
  { id: "word", title: "Word tools", icon: FileType2, accent: "from-sky-500/10 to-sky-500/0" },
  { id: "image", title: "Image tools", icon: ImageIcon, accent: "from-emerald-500/10 to-emerald-500/0" },
  { id: "other", title: "Other formats", icon: FileSpreadsheet, accent: "from-violet-500/10 to-violet-500/0" },
];

const STEPS = [
  { title: "Choose a conversion", body: "Pick from 30+ tools for PDF, Word, images and spreadsheets." },
  { title: "Select your files", body: "Drag, paste or browse. Multiple files are supported where it makes sense." },
  { title: "Set the options", body: "Resolution, page ranges, passwords and quality — only what matters." },
  { title: "Download the result", body: "Files are validated, then deleted from the server automatically." },
];

export function HomePage() {
  const { catalog, loading } = useCatalog();
  const { capabilities } = useCapabilities();
  const retention = capabilities?.limits.retentionMinutes ?? 30;
  const navigate = useNavigate();
  const { push } = useToast();
  const [picked, setPicked] = useState<File[] | null>(null);

  const tools = catalog?.tools ?? [];
  const featured = useMemo(() => tools.filter((tool) => tool.featured).slice(0, 8), [tools]);

  const suggestions = useMemo(() => {
    if (!picked?.length) return [];
    const extensions = new Set(picked.map((file) => file.name.split(".").pop()?.toLowerCase() ?? ""));
    return tools
      .filter((tool) => tool.available && tool.input.extensions.some((ext) => extensions.has(ext)))
      .slice(0, 4);
  }, [picked, tools]);

  const handleFiles = (files: File[]) => {
    if (!files.length) return;
    setPicked(files);
    setPendingFiles(files);
    if (files.length > 1) push(`${files.length} files ready — choose a conversion.`, "info");
  };

  const goToTool = (toolId: string) => {
    if (picked?.length) setPendingFiles(picked);
    navigate(`/tool/${toolId}`);
  };

  return (
    <div className="space-y-12 sm:space-y-16">
      <section className="grid items-start gap-8 lg:grid-cols-[1.05fr,minmax(0,.95fr)] lg:gap-12">
        <div className="animate-fade-up">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-raised px-3 py-1 text-[11.5px] font-medium text-muted">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            Private by design · no account required
          </span>
          <h1 className="mt-5 text-[2.1rem] font-semibold leading-[1.1] tracking-[-0.02em] text-content sm:text-[2.75rem]">
            Every document, ready for
            <span className="relative ml-2 inline-block">
              <span className="relative z-10 text-brand-700 dark:text-brand-300">what&apos;s next</span>
              <span
                aria-hidden="true"
                className="absolute inset-x-0 bottom-1 z-0 h-2.5 rounded-sm bg-brand-200/60 dark:bg-brand-800/50"
              />
            </span>
            .
          </h1>
          <p className="mt-4 max-w-xl text-[14.5px] leading-relaxed text-muted">
            Convert PDFs to editable Word, render pages to images, merge, split, compress, protect and run OCR —
            on a conversion server you can trust, with automatic deletion of every upload.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-2.5">
            <Link to="/tools" className="btn-primary">
              Browse all tools
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link to="/tool/pdf-to-word" className="btn-secondary">
              <Sparkles className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
              PDF to Word
            </Link>
          </div>

          <dl className="mt-8 grid grid-cols-3 gap-4 border-t border-line pt-5">
            <div>
              <dt className="text-[11px] uppercase tracking-wide text-muted">Tools</dt>
              <dd className="mt-0.5 text-lg font-semibold text-content">{loading ? "—" : tools.length}</dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-wide text-muted">Retention</dt>
              <dd className="mt-0.5 text-lg font-semibold text-content">{retention} min</dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-wide text-muted">Account</dt>
              <dd className="mt-0.5 text-lg font-semibold text-content">Not needed</dd>
            </div>
          </dl>
        </div>

        <div className="animate-fade-up rounded-2xl border border-line bg-raised/80 p-3 shadow-card backdrop-blur sm:p-4">
          <Dropzone
            accept={ALL_EXTENSIONS}
            multiple
            maxFiles={20}
            onFiles={handleFiles}
            label="Choose a file or drag it here"
            hint="PDF · Word · Excel · PowerPoint · images · text"
          />
          {picked && picked.length > 0 && (
            <div className="mt-3 rounded-xl border border-line bg-sunken/60 p-3.5">
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-[12.5px] font-medium text-content">
                  {picked.length === 1 ? picked[0].name : `${picked.length} files selected`}
                </p>
                <button
                  type="button"
                  className="text-[11.5px] font-medium text-muted hover:text-content"
                  onClick={() => setPicked(null)}
                >
                  Clear
                </button>
              </div>
              <p className="mt-1 text-[11.5px] text-muted">Recommended tools for this file:</p>
              <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
                {suggestions.map((tool) => (
                  <button
                    key={tool.id}
                    type="button"
                    onClick={() => goToTool(tool.id)}
                    className="flex items-center justify-between gap-2 rounded-lg border border-line bg-raised px-3 py-2 text-left text-[12px] font-medium text-content transition-colors hover:border-brand-300 hover:text-brand-700 dark:hover:border-brand-800 dark:hover:text-brand-300"
                  >
                    <span className="truncate">{tool.title}</span>
                    <ArrowRight className="h-3.5 w-3.5 shrink-0 opacity-60" aria-hidden="true" />
                  </button>
                ))}
                {suggestions.length === 0 && (
                  <p className="text-[11.5px] text-muted">
                    No tool accepts this format yet.{" "}
                    <Link to="/tools" className="underline">
                      See supported formats
                    </Link>
                    .
                  </p>
                )}
              </div>
            </div>
          )}
          <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-muted sm:grid-cols-3">
            {[
              { icon: Lock, label: "Encrypted uploads" },
              { icon: Trash2, label: "Auto-deleted files" },
              { icon: BadgeCheck, label: "Validated output" },
            ].map(({ icon: Icon, label }) => (
              <span key={label} className="flex items-center gap-1.5">
                <Icon className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                {label}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="categories-heading">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 id="categories-heading" className="text-lg font-semibold tracking-tight text-content">
              Start from a category
            </h2>
            <p className="mt-1 text-[13px] text-muted">Everything is grouped the way you think about documents.</p>
          </div>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {CATEGORY_ART.map(({ id, title, icon: Icon, accent }) => {
            const category = catalog?.categories.find((item) => item.id === id);
            const count = tools.filter((tool) => tool.category === id).length;
            return (
              <Link
                key={id}
                to={`/tools?category=${id}`}
                className={`group relative overflow-hidden rounded-2xl border border-line bg-raised p-4 shadow-card transition-all hover:-translate-y-0.5 hover:shadow-lift`}
              >
                <span className={`absolute inset-0 bg-gradient-to-br ${accent}`} aria-hidden="true" />
                <span className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-surface text-content">
                  <Icon className="h-[18px] w-[18px]" strokeWidth={1.9} aria-hidden="true" />
                </span>
                <h3 className="relative mt-3 text-[14px] font-semibold text-content">{category?.label ?? title}</h3>
                <p className="relative mt-0.5 text-[12px] text-muted">{count} tools</p>
                <ArrowRight
                  className="absolute bottom-4 right-4 h-4 w-4 text-muted/50 transition-transform group-hover:translate-x-0.5"
                  aria-hidden="true"
                />
              </Link>
            );
          })}
        </div>
      </section>

      <section aria-labelledby="featured-heading">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 id="featured-heading" className="text-lg font-semibold tracking-tight text-content">
              Most used conversions
            </h2>
            <p className="mt-1 text-[13px] text-muted">Polished defaults, adjustable when you need control.</p>
          </div>
          <Link
            to="/tools"
            className="hidden items-center gap-1 text-[12.5px] font-medium text-brand-700 hover:underline sm:flex dark:text-brand-300"
          >
            All tools <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        </div>
        {loading && !featured.length ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="card h-[148px] p-4">
                <div className="skeleton h-10 w-10 rounded-xl" />
                <div className="skeleton mt-4 h-3.5 w-3/4" />
                <div className="skeleton mt-2.5 h-3 w-1/2" />
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {featured.map((tool) => (
              <ToolCard key={tool.id} tool={tool} />
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="how-heading" className="rounded-2xl border border-line bg-raised p-5 shadow-card sm:p-7">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          <h2 id="how-heading" className="text-[15px] font-semibold text-content">
            Four steps, no account
          </h2>
        </div>
        <ol className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => (
            <li key={step.title} className="relative">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-line bg-sunken text-[12px] font-semibold text-content">
                {index + 1}
              </span>
              <h3 className="mt-2.5 text-[13px] font-semibold text-content">{step.title}</h3>
              <p className="mt-1 text-[12px] leading-relaxed text-muted">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="overflow-hidden rounded-2xl border border-emerald-200/70 bg-emerald-50/50 p-5 sm:p-7 dark:border-emerald-900/50 dark:bg-emerald-950/20">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="max-w-2xl">
            <h2 className="flex items-center gap-2 text-[15px] font-semibold text-emerald-950 dark:text-emerald-100">
              <ShieldCheck className="h-4 w-4" aria-hidden="true" />
              Your documents stay yours
            </h2>
            <p className="mt-2 text-[12.5px] leading-relaxed text-emerald-900/80 dark:text-emerald-200/80">
              Conversions run on a dedicated service, never in a third-party public endpoint. Uploads are
              signature-checked, processed in isolated workers, and deleted automatically — immediately after
              download or after the retention window. Files are never used for model training.
            </p>
            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-[11.5px] text-emerald-900/70 dark:text-emerald-200/70">
              <span className="flex items-center gap-1.5">
                <Clock3 className="h-3.5 w-3.5" aria-hidden="true" /> {retention}-minute maximum retention
              </span>
              <span className="flex items-center gap-1.5">
                <Lock className="h-3.5 w-3.5" aria-hidden="true" /> Token-protected downloads
              </span>
              <span className="flex items-center gap-1.5">
                <Trash2 className="h-3.5 w-3.5" aria-hidden="true" /> One-click deletion
              </span>
            </div>
          </div>
          <Link to="/privacy" className="btn-secondary shrink-0">
            Read the privacy policy
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      </section>
    </div>
  );
}
