import { Link } from "react-router-dom";

/** DOCUPRO mark: a folded sheet with a conversion arrow. */
export function LogoMark({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <rect width="40" height="40" rx="11" fill="url(#docupro-mark)" />
      <path
        d="M13.5 10.5h9.2l5.3 5.3v13.7a2 2 0 0 1-2 2H13.5a2 2 0 0 1-2-2V12.5a2 2 0 0 1 2-2Z"
        fill="#fff"
        fillOpacity=".97"
      />
      <path d="M22.7 10.5l5.3 5.3h-4.1a1.2 1.2 0 0 1-1.2-1.2v-4.1Z" fill="#bfd3fe" />
      <path
        d="M16 20.2h6.6m0 0-2.2-2.2m2.2 2.2-2.2 2.2"
        stroke="#254deb"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M16 25.4h7.6" stroke="#93b4fd" strokeWidth="1.7" strokeLinecap="round" />
      <defs>
        <linearGradient id="docupro-mark" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop stopColor="#3b6bf6" />
          <stop offset="1" stopColor="#1d3ad8" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export function Wordmark({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="group flex items-center gap-2.5 rounded-xl" aria-label="DOCUPRO home">
      <LogoMark className="h-8 w-8 shrink-0 transition-transform duration-200 group-hover:-rotate-3" />
      <span className="flex flex-col leading-none">
        <span className="text-[15px] font-bold tracking-[0.14em] text-content">DOCUPRO</span>
        {!compact && (
          <span className="mt-1 text-[10px] font-medium uppercase tracking-[0.16em] text-muted">
            Document converter
          </span>
        )}
      </span>
    </Link>
  );
}
