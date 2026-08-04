"use client";

import * as React from "react";
import { useShellStore } from "@/store/shell-store";

/**
 * Global keyboard shortcuts for the application shell.
 * Ctrl/Cmd+K is owned by CommandPalette.
 */
export function useShellShortcuts() {
  const setGlobalSearchOpen = useShellStore((s) => s.setGlobalSearchOpen);
  const setMobileNavOpen = useShellStore((s) => s.setMobileNavOpen);

  React.useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName?.toLowerCase();
      const editable =
        tag === "input" ||
        tag === "textarea" ||
        tag === "select" ||
        target?.isContentEditable;

      if (event.key === "Escape") {
        setMobileNavOpen(false);
        return;
      }

      if (editable) return;

      if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        event.preventDefault();
        setGlobalSearchOpen(true);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [setGlobalSearchOpen, setMobileNavOpen]);
}
