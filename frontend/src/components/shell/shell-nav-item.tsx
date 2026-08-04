"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { NavItem } from "@/config/navigation";

type ShellNavItemProps = {
  item: NavItem;
  collapsed?: boolean;
  depth?: number;
  onNavigate?: () => void;
};

function isActivePath(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function ShellNavItem({
  item,
  collapsed = false,
  depth = 0,
  onNavigate,
}: ShellNavItemProps) {
  const pathname = usePathname();
  const hasChildren = Boolean(item.children?.length);
  const active = isActivePath(pathname, item.href);
  const childActive = item.children?.some((child) => isActivePath(pathname, child.href));
  const [open, setOpen] = React.useState(Boolean(childActive || active));

  React.useEffect(() => {
    if (childActive || active) setOpen(true);
  }, [childActive, active]);

  const Icon = item.icon;
  const badgeTone = item.badge?.tone ?? "muted";
  const disabled = Boolean(item.disabled);

  const content = (
    <span
      className={cn(
        "group flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        "text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
        (active || childActive) && "bg-sidebar-accent text-sidebar-foreground",
        collapsed && "justify-center px-2",
        depth > 0 && !collapsed && "pl-9",
        disabled && "pointer-events-none opacity-50",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
      {!collapsed ? (
        <>
          <span className="min-w-0 flex-1 truncate text-left">{item.label}</span>
          {item.badge ? (
            <Badge variant={badgeTone === "default" ? "secondary" : badgeTone} className="h-5 px-1.5">
              {item.badge.label}
            </Badge>
          ) : null}
          {hasChildren ? (
            <ChevronDown
              className={cn(
                "h-4 w-4 shrink-0 opacity-70 transition-transform",
                open && "rotate-180",
              )}
              aria-hidden="true"
            />
          ) : null}
        </>
      ) : null}
    </span>
  );

  const linkOrButton = hasChildren && !collapsed ? (
    <button
      type="button"
      className="w-full"
      aria-expanded={open}
      aria-controls={`nav-sub-${item.id}`}
      onClick={() => setOpen((v) => !v)}
    >
      {content}
    </button>
  ) : disabled ? (
    <div
      aria-disabled="true"
      title={collapsed ? `${item.label} (unavailable)` : undefined}
      className="block w-full"
    >
      {content}
    </div>
  ) : (
    <Link
      href={item.href}
      aria-current={active ? "page" : undefined}
      title={collapsed ? item.label : undefined}
      onClick={onNavigate}
      className="block w-full"
    >
      {content}
    </Link>
  );

  const wrapped =
    collapsed ? (
      <Tooltip delayDuration={0}>
        <TooltipTrigger asChild>{linkOrButton}</TooltipTrigger>
        <TooltipContent side="right">{item.label}</TooltipContent>
      </Tooltip>
    ) : (
      linkOrButton
    );

  return (
    <div>
      {wrapped}
      {hasChildren && !collapsed ? (
        <AnimatePresence initial={false}>
          {open ? (
            <motion.div
              id={`nav-sub-${item.id}`}
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <ul className="mt-0.5 space-y-0.5" role="list">
                {item.children!.map((child) => (
                  <li key={child.id}>
                    <ShellNavItem
                      item={child}
                      collapsed={false}
                      depth={depth + 1}
                      onNavigate={onNavigate}
                    />
                  </li>
                ))}
              </ul>
            </motion.div>
          ) : null}
        </AnimatePresence>
      ) : null}
    </div>
  );
}
