"use client";

import Link from "next/link";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { brand, navigationSections } from "@/config/navigation";
import { useShellStore } from "@/store/shell-store";
import { ShellNavItem } from "@/components/shell/shell-nav-item";

type AppSidebarProps = {
  onNavigate?: () => void;
  className?: string;
  /** Force expanded (e.g. mobile drawer) */
  forceExpanded?: boolean;
};

export function AppSidebar({ onNavigate, className, forceExpanded = false }: AppSidebarProps) {
  const sidebarCollapsed = useShellStore((s) => s.sidebarCollapsed);
  const toggleSidebarCollapsed = useShellStore((s) => s.toggleSidebarCollapsed);
  const collapsed = forceExpanded ? false : sidebarCollapsed;
  const BrandIcon = brand.icon;

  return (
    <div className={cn("flex h-full w-full flex-col bg-sidebar text-sidebar-foreground", className)}>
      <div
        className={cn(
          "flex h-14 items-center gap-2 border-b border-sidebar-border px-3",
          collapsed && "justify-center px-2",
        )}
      >
        <Link
          href="/dashboard"
          className={cn(
            "flex min-w-0 items-center gap-2 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
            collapsed && "justify-center",
          )}
          onClick={onNavigate}
        >
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-sidebar-accent text-sidebar-ring">
            <BrandIcon className="h-4 w-4" aria-hidden="true" />
          </span>
          {!collapsed ? (
            <span className="truncate text-sm font-semibold tracking-tight">{brand.name}</span>
          ) : (
            <span className="sr-only">{brand.name}</span>
          )}
        </Link>
        {!forceExpanded ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={cn(
              "ml-auto h-8 w-8 text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground",
              collapsed && "ml-0",
            )}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-pressed={collapsed}
            onClick={toggleSidebarCollapsed}
          >
            {collapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </Button>
        ) : null}
      </div>

      <ScrollArea className="flex-1 px-2 py-3">
        <nav aria-label="Primary" className="space-y-4">
          {navigationSections.map((section) => (
            <div key={section.id} role="group" aria-label={section.label}>
              {!collapsed ? (
                <p className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">
                  {section.label}
                </p>
              ) : (
                <Separator className="mb-2 bg-sidebar-border" />
              )}
              <ul className="space-y-0.5" role="list">
                {section.items.map((item) => (
                  <li key={item.id}>
                    <ShellNavItem item={item} collapsed={collapsed} onNavigate={onNavigate} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </ScrollArea>

      <div
        className={cn(
          "border-t border-sidebar-border p-3 text-[11px] text-sidebar-muted",
          collapsed && "px-2 text-center",
        )}
      >
        {collapsed ? "v0.1" : "Enterprise Decision Platform · v0.1"}
      </div>
    </div>
  );
}
