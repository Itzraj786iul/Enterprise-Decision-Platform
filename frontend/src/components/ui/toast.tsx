"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, AlertTriangle, XCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type ToastVariant = "default" | "success" | "warning" | "danger" | "info";

export type ToastItem = {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  durationMs?: number;
};

type ToastContextValue = {
  toasts: ToastItem[];
  toast: (item: Omit<ToastItem, "id">) => void;
  dismiss: (id: string) => void;
};

const ToastContext = React.createContext<ToastContextValue | null>(null);

const icons: Record<ToastVariant, React.ReactNode> = {
  default: <Info className="h-4 w-4" aria-hidden="true" />,
  success: <CheckCircle2 className="h-4 w-4 text-success" aria-hidden="true" />,
  warning: <AlertTriangle className="h-4 w-4 text-warning" aria-hidden="true" />,
  danger: <XCircle className="h-4 w-4 text-danger" aria-hidden="true" />,
  info: <Info className="h-4 w-4 text-info" aria-hidden="true" />,
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastItem[]>([]);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => setMounted(true), []);

  const dismiss = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = React.useCallback(
    (item: Omit<ToastItem, "id">) => {
      const id = crypto.randomUUID();
      const duration = item.durationMs ?? 4000;
      setToasts((prev) => [...prev, { ...item, id }]);
      window.setTimeout(() => dismiss(id), duration);
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      {mounted
        ? createPortal(
            <div
              className="pointer-events-none fixed bottom-4 right-4 z-[70] flex w-full max-w-sm flex-col gap-2"
              aria-live="polite"
              aria-relevant="additions"
            >
              <AnimatePresence initial={false}>
                {toasts.map((item) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 12, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 8, scale: 0.98 }}
                    transition={{ duration: 0.2 }}
                    className={cn(
                      "pointer-events-auto flex items-start gap-3 rounded-lg border border-border bg-card p-4 shadow-lg",
                    )}
                    role="status"
                  >
                    <span className="mt-0.5">{icons[item.variant ?? "default"]}</span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">{item.title}</p>
                      {item.description ? (
                        <p className="mt-0.5 text-sm text-muted-foreground">{item.description}</p>
                      ) : null}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      aria-label="Dismiss notification"
                      onClick={() => dismiss(item.id)}
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>,
            document.body,
          )
        : null}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
