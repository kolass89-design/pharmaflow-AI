import { Link } from "react-router-dom";
import { Cpu, ExternalLink, Gauge, Layers, Smartphone, Sparkles } from "lucide-react";
import { useCapabilities } from "@/lib/hooks";
import { LogoMark } from "@/components/Logo";

const ENGINES = [
  { name: "MuPDF / PyMuPDF", role: "PDF rendering, page operations, text extraction, AES-256 encryption" },
  { name: "pdf2docx", role: "Layout-aware PDF → Word reconstruction (headings, tables, images)" },
  { name: "Tesseract or ONNX OCR", role: "Searchable PDFs, image → text, scanned PDF → Word" },
  { name: "python-docx + PyMuPDF Story", role: "Built-in Word renderer when LibreOffice is absent" },
  { name: "LibreOffice (optional)", role: "Highest fidelity Office rendering and legacy .doc support" },
  { name: "Pillow, pillow-heif, openpyxl", role: "Image pipeline, HEIC support and spreadsheet conversion" },
];

export function AboutPage() {
  const { capabilities } = useCapabilities();
  const version = capabilities?.version ?? "1.0.0";

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header className="flex items-start gap-4">
        <LogoMark className="h-14 w-14 shrink-0" />
        <div>
          <h1 className="text-[1.7rem] font-semibold tracking-tight text-content sm:text-[2rem]">DOCUPRO</h1>
          <p className="mt-1 text-[13.5px] text-muted">
            Smart Document Converter · version {version} · cross-platform
          </p>
        </div>
      </header>

      <section className="card p-5 sm:p-6">
        <h2 className="flex items-center gap-2 text-[15px] font-semibold text-content">
          <Sparkles className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          What DOCUPRO is
        </h2>
        <p className="mt-2 text-[13px] leading-relaxed text-muted">
          A complete document-conversion product for PDF, Word, images, spreadsheets and text. It runs its own
          conversion service — no public “free converter” endpoint — with background jobs, progress reporting,
          validated outputs and a strict retention policy. The same engine serves the web app, the Windows desktop
          app and the Android app.
        </p>
        <div className="mt-4 grid gap-2 text-[12px] sm:grid-cols-3">
          {[
            { icon: Layers, label: "37 tools", detail: "PDF, Word, images, other formats" },
            { icon: Cpu, label: "Shared engine", detail: "One API for every client" },
            { icon: Smartphone, label: "Cross-platform", detail: "Web, Windows, Android" },
          ].map(({ icon: Icon, label, detail }) => (
            <div key={label} className="rounded-xl border border-line bg-sunken/50 p-3">
              <Icon className="h-4 w-4 text-muted" aria-hidden="true" />
              <p className="mt-2 text-[12px] font-semibold text-content">{label}</p>
              <p className="text-[11px] text-muted">{detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="flex items-center gap-2 text-[15px] font-semibold text-content">
          <Cpu className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          Conversion engines on this server
        </h2>
        <ul className="mt-3 divide-y divide-line overflow-hidden rounded-xl border border-line bg-raised">
          {ENGINES.map((engine) => (
            <li key={engine.name} className="px-4 py-3">
              <p className="text-[12.5px] font-medium text-content">{engine.name}</p>
              <p className="mt-0.5 text-[11.5px] leading-relaxed text-muted">{engine.role}</p>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[11.5px] text-muted">
          Detected on this instance: PDF via {capabilities?.engines.pdf ?? "MuPDF"} · Word renderer:{" "}
          {capabilities?.engines.docxRender ?? "built-in"} · OCR: {capabilities?.engines.ocr ?? "not installed"}.
        </p>
      </section>

      <section>
        <h2 className="flex items-center gap-2 text-[15px] font-semibold text-content">
          <Gauge className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          Design principles
        </h2>
        <ul className="mt-2.5 space-y-2 text-[12.5px] leading-relaxed text-muted">
          <li>
            <span className="font-medium text-content">Honest capabilities.</span>{" "}
            Tools that need an engine the server does not have are marked unavailable with the reason, instead of
            failing after upload.
          </li>
          <li>
            <span className="font-medium text-content">Nothing pretends to work.</span> Every advertised conversion has
            a backend implementation and an automated test; outputs are validated before download.
          </li>
          <li>
            <span className="font-medium text-content">Minimal moving parts.</span> One API, one worker model, no
            database, no third-party document service. It scales with replicas, not with complexity.
          </li>
          <li>
            <span className="font-medium text-content">Accessible by default.</span> Keyboard-operable dropzone,
            semantic landmarks, visible focus rings, reduced-motion support and WCAG AA contrast in both themes.
          </li>
        </ul>
      </section>

      <section className="rounded-2xl border border-line bg-raised p-5">
        <h2 className="text-[14px] font-semibold text-content">Known limitations</h2>
        <ul className="mt-2 space-y-1.5 text-[12px] leading-relaxed text-muted">
          <li>· Exact layout reconstruction of complex PDFs and formulas is best-effort; OCR cannot recover original fonts.</li>
          <li>· PowerPoint to PDF and legacy .doc conversion require LibreOffice, which may not be installed on every host.</li>
          <li>· The built-in Word renderer preserves structure but may differ from Word pagination; extracted text can contain ligature glyphs (ﬁ, ﬀ).</li>
          <li>· PDF to Excel detects ruled tables; scanned tables need OCR first.</li>
          <li>· Very large documents are capped by configurable page, pixel and size limits.</li>
        </ul>
      </section>

      <section className="text-[12px] leading-relaxed text-muted">
        <h2 className="text-[14px] font-semibold text-content">Source and licensing</h2>
        <p className="mt-2">
          DOCUPRO is delivered as source code with build instructions for the API, the web app, the Windows desktop
          app (Tauri) and the Android app. Third-party components keep their own licences; see the repository&apos;s
          LICENSE and NOTICE files.
        </p>
        <p className="mt-3 flex flex-wrap gap-3">
          <Link to="/privacy" className="inline-flex items-center gap-1 font-medium text-brand-700 hover:underline dark:text-brand-300">
            Privacy & security
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </Link>
          <Link to="/settings" className="inline-flex items-center gap-1 font-medium text-brand-700 hover:underline dark:text-brand-300">
            App settings
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </Link>
        </p>
      </section>
    </div>
  );
}
