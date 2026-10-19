import { Link } from "react-router-dom";
import { Clock3, Database, EyeOff, FileLock2, KeyRound, Lock, ServerCog, ShieldCheck, Trash2 } from "lucide-react";
import { useCapabilities } from "@/lib/hooks";
import { formatBytes, formatMinutes } from "@/lib/format";

const MEASURES = [
  {
    icon: FileLock2,
    title: "Validated uploads",
    body: "Every file is checked against its extension and its real byte signature. Office packages are screened for compression bombs and unsafe internal paths before any parser opens them.",
  },
  {
    icon: KeyRound,
    title: "Token-protected downloads",
    body: "Each job gets an unguessable 128-bit identifier and a separate download token. Expired jobs return nothing, and file paths are never exposed to the browser.",
  },
  {
    icon: ServerCog,
    title: "Isolated workers",
    body: "Conversions run in a short-lived process per job with a CPU limit, file-size limit and timeout. A crash or a malicious document cannot take down the API or touch other jobs.",
  },
  {
    icon: ShieldCheck,
    title: "Validated output",
    body: "Generated PDFs, DOCX files, spreadsheets and images are reopened and parsed before a download link is shown. A conversion never reports success with a broken file.",
  },
];

export function PrivacyPage() {
  const { capabilities } = useCapabilities();
  const retention = capabilities?.limits.retentionMinutes ?? 30;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-raised px-3 py-1 text-[11px] font-medium text-muted">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          Privacy & security
        </span>
        <h1 className="mt-4 text-[1.7rem] font-semibold tracking-tight text-content sm:text-[2rem]">
          Documents are confidential by default
        </h1>
        <p className="mt-2 text-[13.5px] leading-relaxed text-muted">
          DOCUPRO converts school, business and financial documents. The service is designed so that your files
          exist for as short a time as technically possible, and so that nobody can reach them without the link you
          received.
        </p>
      </header>

      <section className="card p-5 sm:p-6" aria-labelledby="retention">
        <h2 id="retention" className="flex items-center gap-2 text-[15px] font-semibold text-content">
          <Clock3 className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          Retention policy
        </h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          {[
            { icon: Trash2, label: "Uploads", value: "Deleted when the job ends" },
            { icon: Clock3, label: "Results", value: `${formatMinutes(retention)} maximum` },
            { icon: Lock, label: "After download", value: "Removed within 2 minutes" },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="rounded-xl border border-line bg-sunken/50 p-3">
              <Icon className="h-4 w-4 text-muted" aria-hidden="true" />
              <p className="mt-2 text-[11px] uppercase tracking-wide text-muted">{label}</p>
              <p className="mt-0.5 text-[12.5px] font-medium text-content">{value}</p>
            </div>
          ))}
        </div>
        <ul className="mt-4 space-y-2 text-[12.5px] leading-relaxed text-muted">
          <li>
            Source files are removed from disk as soon as the conversion finishes. Converted files stay available
            until every artifact has been downloaded (plus a two-minute grace period), until you press “Delete files
            now”, or until the retention window ends — whichever comes first.
          </li>
          <li>
            A background sweeper deletes expired job directories every 30 seconds. A restart of the service also
            clears orphaned working directories.
          </li>
          <li>Nothing is copied to a database: job state is ephemeral and lives in memory plus a private temp directory.</li>
        </ul>
      </section>

      <section aria-labelledby="stored">
        <h2 id="stored" className="flex items-center gap-2 text-[15px] font-semibold text-content">
          <Database className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          What is stored, and where
        </h2>
        <div className="mt-3 overflow-hidden rounded-xl border border-line">
          <table className="w-full text-left text-[12.5px]">
            <thead className="bg-sunken/70 text-[11px] uppercase tracking-wide text-muted">
              <tr>
                <th scope="col" className="px-4 py-2.5 font-semibold">Data</th>
                <th scope="col" className="px-4 py-2.5 font-semibold">Where</th>
                <th scope="col" className="px-4 py-2.5 font-semibold">Lifetime</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              <tr>
                <td className="px-4 py-2.5 text-content">Your document contents</td>
                <td className="px-4 py-2.5 text-muted">Conversion server temp storage</td>
                <td className="px-4 py-2.5 text-muted">Minutes (see above)</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-content">File names, sizes and job status</td>
                <td className="px-4 py-2.5 text-muted">Server memory while the job runs</td>
                <td className="px-4 py-2.5 text-muted">Until expiry</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-content">Theme, preferences, optional history and its short-lived download links</td>
                <td className="px-4 py-2.5 text-muted">This browser only (localStorage)</td>
                <td className="px-4 py-2.5 text-muted">Until you clear it</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-content">Accounts, profiles, analytics</td>
                <td className="px-4 py-2.5 text-muted">Not collected</td>
                <td className="px-4 py-2.5 text-muted">—</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="measures">
        <h2 id="measures" className="flex items-center gap-2 text-[15px] font-semibold text-content">
          <Lock className="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          Security measures in place
        </h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {MEASURES.map(({ icon: Icon, title, body }) => (
            <div key={title} className="card p-4">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700 dark:bg-brand-950/40 dark:text-brand-300">
                <Icon className="h-4 w-4" aria-hidden="true" />
              </span>
              <h3 className="mt-2.5 text-[12.5px] font-semibold text-content">{title}</h3>
              <p className="mt-1 text-[11.5px] leading-relaxed text-muted">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-line bg-raised p-5">
        <h2 className="flex items-center gap-2 text-[14px] font-semibold text-content">
          <EyeOff className="h-4 w-4 text-muted" aria-hidden="true" />
          What DOCUPRO never does
        </h2>
        <ul className="mt-2.5 grid gap-1.5 text-[12.5px] leading-relaxed text-muted sm:grid-cols-2">
          <li>· Train models on your documents</li>
          <li>· Require an account to convert a file</li>
          <li>· Share documents with third-party converters</li>
          <li>· Keep logs containing document contents</li>
          <li>· Track you across other websites</li>
          <li>· Publish or index any converted file</li>
        </ul>
      </section>

      <section className="text-[12.5px] leading-relaxed text-muted">
        <h2 className="text-[14px] font-semibold text-content">Limits and transparency</h2>
        <p className="mt-2">
          Uploads are limited to {capabilities ? formatBytes(capabilities.limits.maxUploadBytes) : "50 MB"} per file
          and {capabilities ? formatBytes(capabilities.limits.maxJobBytes) : "200 MB"} per job; PDFs to{" "}
          {capabilities?.limits.maxPages ?? 500} pages. Rate limits protect the service from abuse and are applied
          per client address. If you administer the service, every limit can be changed through environment
          variables documented in the deployment guide.
        </p>
        <p className="mt-2">
          Conversions require a network connection. The interface itself is cached for offline use. Results are
          delivered over the same origin; no third-party CDN, font service or analytics script is loaded.
        </p>
        <p className="mt-4">
          Questions about a deployment? See <Link to="/about" className="font-medium text-brand-700 underline dark:text-brand-300">About</Link>{" "}
          or contact the operator of this DOCUPRO instance.
        </p>
      </section>
    </div>
  );
}
