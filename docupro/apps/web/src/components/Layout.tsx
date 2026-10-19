import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  FileSpreadsheet,
  FileText,
  FileType2,
  History,
  Home,
  Image as ImageIcon,
  LayoutGrid,
  Menu,
  Settings,
  ShieldCheck,
  X,
} from "lucide-react";
import { Wordmark } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";
import { useTheme } from "@/lib/hooks";

const PRIMARY = [
  { to: "/", label: "Home", icon: Home, end: true },
  { to: "/tools", label: "All tools", icon: LayoutGrid },
];

const CATEGORIES = [
  { to: "/tools?category=pdf", key: "pdf", label: "PDF tools", icon: FileText },
  { to: "/tools?category=word", key: "word", label: "Word tools", icon: FileType2 },
  { to: "/tools?category=image", key: "image", label: "Image tools", icon: ImageIcon },
  { to: "/tools?category=other", key: "other", label: "Other formats", icon: FileSpreadsheet },
];

const SECONDARY = [
  { to: "/recent", label: "Recent conversions", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];

function NavItem({
  to,
  label,
  icon: Icon,
  end,
  active,
  onClick,
}: {
  to: string;
  label: string;
  icon: typeof Home;
  end?: boolean;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
      className={({ isActive }) =>
        `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13.5px] font-medium transition-colors ${
          (active ?? isActive)
            ? "bg-ink-900 text-white shadow-sm dark:bg-white/10 dark:text-white"
            : "text-muted hover:bg-sunken hover:text-content"
        }`
      }
    >
      <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.9} aria-hidden="true" />
      <span className="truncate">{label}</span>
    </NavLink>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const category = params.get("category");
  const { preference, setPreference } = useTheme();

  return (
    <div className="flex h-full flex-col">
      <div className="px-4 pb-5 pt-5">
        <Wordmark />
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-3" aria-label="Main navigation">
        {PRIMARY.map((item) => (
          <NavItem key={item.to} {...item} onClick={onNavigate} />
        ))}
        <p className="px-3 pb-1.5 pt-5 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-muted/80">
          Categories
        </p>
        {CATEGORIES.map((item) => (
          <NavItem
            key={item.to}
            to={item.to}
            label={item.label}
            icon={item.icon}
            active={location.pathname === "/tools" && category === item.key}
            onClick={onNavigate}
          />
        ))}
        <div className="my-3 border-t border-line" />
        {SECONDARY.map((item) => (
          <NavItem key={item.to} {...item} onClick={onNavigate} />
        ))}
      </nav>
      <div className="space-y-3 border-t border-line p-3">
        <div className="flex items-center justify-between gap-2 px-1">
          <span className="text-[11px] font-medium text-muted">Appearance</span>
          <ThemeToggle preference={preference} onChange={setPreference} compact />
        </div>
        <Link
          to="/privacy"
          onClick={onNavigate}
          className="flex items-center gap-2 rounded-lg px-1 py-1 text-[11.5px] font-medium text-muted transition-colors hover:text-content"
        >
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
          Private by design · auto-delete
        </Link>
      </div>
    </div>
  );
}

export function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMenuOpen(false);
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [location.pathname, location.search]);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  return (
    <div className="min-h-full">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-brand-600 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
      >
        Skip to content
      </a>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-line bg-raised lg:block">
        <SidebarContent />
      </aside>

      {/* Mobile header */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-raised/90 px-4 py-3 backdrop-blur lg:hidden">
        <Wordmark compact />
        <button
          type="button"
          className="icon-btn"
          onClick={() => setMenuOpen(true)}
          aria-label="Open navigation menu"
          aria-expanded={menuOpen}
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
      </header>

      {menuOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-ink-950/50 backdrop-blur-sm"
            onClick={() => setMenuOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute inset-y-0 left-0 w-[82%] max-w-xs animate-fade-up border-r border-line bg-raised shadow-lift">
            <button
              type="button"
              className="icon-btn absolute right-3 top-3"
              onClick={() => setMenuOpen(false)}
              aria-label="Close navigation menu"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
            <SidebarContent onNavigate={() => setMenuOpen(false)} />
          </div>
        </div>
      )}

      <div className="lg:pl-64">
        <main id="main" className="page-glow min-h-[calc(100vh-4rem)]">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-9 lg:px-10">
            <Outlet />
          </div>
        </main>
        <footer className="border-t border-line/70 px-4 py-8 sm:px-6 lg:px-10">
          <div className="mx-auto flex max-w-6xl flex-col gap-3 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
            <p>© {new Date().getFullYear()} DOCUPRO · Smart Document Converter</p>
            <nav className="flex flex-wrap items-center gap-4" aria-label="Footer">
              <Link to="/privacy" className="transition-colors hover:text-content">
                Privacy & security
              </Link>
              <Link to="/about" className="transition-colors hover:text-content">
                About
              </Link>
              <Link to="/settings" className="transition-colors hover:text-content">
                Settings
              </Link>
            </nav>
          </div>
        </footer>
      </div>
    </div>
  );
}
