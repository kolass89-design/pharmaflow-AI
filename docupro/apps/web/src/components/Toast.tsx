import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { CircleAlert, CircleCheck, Info, X } from "lucide-react";

type ToastVariant = "success" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  push: (message: string, variant?: ToastVariant) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const STYLES: Record<ToastVariant, string> = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/70 dark:text-emerald-100",
  error: "border-red-200 bg-red-50 text-red-900 dark:border-red-900/60 dark:bg-red-950/70 dark:text-red-100",
  info: "border-line bg-raised text-content",
};

const ICONS = { success: CircleCheck, error: CircleAlert, info: Info };

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((message: string, variant: ToastVariant = "info") => {
    const id = crypto.randomUUID();
    setToasts((current) => [...current.slice(-2), { id, message, variant }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 5200);
  }, []);

  const value = useMemo(() => ({ push }), [push]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex flex-col items-center gap-2 px-4 sm:bottom-6"
        role="status"
        aria-live="polite"
      >
        {toasts.map((toast) => {
          const Icon = ICONS[toast.variant];
          return (
            <div
              key={toast.id}
              className={`pointer-events-auto flex w-full max-w-md animate-fade-up items-start gap-3 rounded-xl border px-4 py-3 text-sm shadow-lift backdrop-blur ${STYLES[toast.variant]}`}
            >
              <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <p className="flex-1 leading-relaxed">{toast.message}</p>
              <button
                type="button"
                className="rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
                onClick={() => setToasts((current) => current.filter((item) => item.id !== toast.id))}
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside ToastProvider");
  return context;
}
