"use client";

import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useShellStore } from "@/store/shell-store";
import { AppSidebar } from "@/components/shell/app-sidebar";

export function MobileNavDrawer() {
  const open = useShellStore((s) => s.mobileNavOpen);
  const setMobileNavOpen = useShellStore((s) => s.setMobileNavOpen);

  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.div
            key="overlay"
            className="fixed inset-0 z-40 bg-black/50 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setMobileNavOpen(false)}
            aria-hidden="true"
          />
          <motion.aside
            key="drawer"
            className="fixed inset-y-0 left-0 z-50 w-[min(20rem,88vw)] bg-sidebar shadow-lg md:hidden"
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "tween", duration: 0.22 }}
            role="dialog"
            aria-modal="true"
            aria-label="Mobile navigation"
          >
            <div className="absolute right-2 top-2 z-10">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground"
                aria-label="Close navigation"
                onClick={() => setMobileNavOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <AppSidebar forceExpanded onNavigate={() => setMobileNavOpen(false)} />
          </motion.aside>
        </>
      ) : null}
    </AnimatePresence>
  );
}
