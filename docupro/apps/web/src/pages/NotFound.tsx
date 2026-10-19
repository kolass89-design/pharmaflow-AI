import { Link } from "react-router-dom";
import { Compass } from "lucide-react";

export function NotFoundPage() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center py-20 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-sunken text-muted">
        <Compass className="h-6 w-6" aria-hidden="true" />
      </span>
      <h1 className="mt-4 text-xl font-semibold text-content">This page does not exist</h1>
      <p className="mt-1.5 text-[13px] leading-relaxed text-muted">
        The link may be mistyped or outdated. Every tool is one click away from the catalog.
      </p>
      <div className="mt-5 flex gap-2">
        <Link to="/" className="btn-secondary !py-2 text-xs">
          Go home
        </Link>
        <Link to="/tools" className="btn-primary !py-2 text-xs">
          Browse tools
        </Link>
      </div>
    </div>
  );
}
