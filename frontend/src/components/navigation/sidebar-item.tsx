"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

type SidebarItemProps = {
  href: string;
  label: string;
  icon?: React.ReactNode;
  active?: boolean;
  collapsed?: boolean;
  badge?: React.ReactNode;
  className?: string;
};

export function SidebarItem({
  href,
  label,
  icon,
  active = false,
  collapsed = false,
  badge,
  className,
}: SidebarItemProps) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      title={collapsed ? label : undefined}
      className={cn(
        "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-sidebar-muted transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
        active && "bg-sidebar-accent text-sidebar-foreground",
        collapsed && "justify-center px-2",
        className,
      )}
    >
      {icon ? <span className="shrink-0 [&_svg]:h-4 [&_svg]:w-4">{icon}</span> : null}
      {!collapsed ? <span className="truncate">{label}</span> : null}
      {!collapsed && badge ? <span className="ml-auto">{badge}</span> : null}
    </Link>
  );
}
