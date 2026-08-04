"use client";

import * as React from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

type SidebarProps = {
  brand?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  collapsed?: boolean;
  className?: string;
};

export function Sidebar({ brand, children, footer, collapsed = false, className }: SidebarProps) {
  return (
    <div className={cn("flex h-full w-full flex-col", className)}>
      <div
        className={cn(
          "flex h-14 items-center border-b border-sidebar-border px-4",
          collapsed && "justify-center px-2",
        )}
      >
        {brand}
      </div>
      <ScrollArea className="flex-1 px-2 py-3">
        <nav aria-label="Sidebar" className="flex flex-col gap-1">
          {children}
        </nav>
      </ScrollArea>
      {footer ? (
        <div className={cn("border-t border-sidebar-border p-3", collapsed && "px-2")}>
          {footer}
        </div>
      ) : null}
    </div>
  );
}
