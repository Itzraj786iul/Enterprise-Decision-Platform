"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type AppShellProps = {
  sidebar: React.ReactNode;
  navbar: React.ReactNode;
  children: React.ReactNode;
  sidebarCollapsed?: boolean;
  className?: string;
};

/**
 * Application chrome: sticky top navbar + collapsible sidebar + main content.
 */
export function AppShell({
  sidebar,
  navbar,
  children,
  sidebarCollapsed = false,
  className,
}: AppShellProps) {
  return (
    <div className={cn("flex min-h-screen bg-background", className)}>
      <aside
        className={cn(
          "sticky top-0 z-20 hidden h-screen shrink-0 border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-[width] duration-300 md:flex md:flex-col",
          sidebarCollapsed ? "w-[4.5rem]" : "w-64",
        )}
        aria-label="Primary"
      >
        {sidebar}
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
          {navbar}
        </header>
        <main id="main-content" className="flex-1 outline-none" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
