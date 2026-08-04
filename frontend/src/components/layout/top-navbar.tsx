"use client";

import * as React from "react";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type TopNavbarProps = {
  title?: string;
  onMenuClick?: () => void;
  leading?: React.ReactNode;
  trailing?: React.ReactNode;
  className?: string;
};

export function TopNavbar({
  title,
  onMenuClick,
  leading,
  trailing,
  className,
}: TopNavbarProps) {
  return (
    <div
      className={cn(
        "flex h-14 items-center gap-3 px-3 sm:px-4 lg:px-6",
        className,
      )}
    >
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        aria-label="Open navigation menu"
        onClick={onMenuClick}
      >
        <Menu className="h-5 w-5" />
      </Button>
      {leading}
      {title ? (
        <p className="truncate text-sm font-semibold tracking-tight text-foreground sm:text-base">
          {title}
        </p>
      ) : null}
      <div className="ml-auto flex items-center gap-1 sm:gap-2">{trailing}</div>
    </div>
  );
}
