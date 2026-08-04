"use client";

import type { ReactNode } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { Breadcrumbs, type BreadcrumbItem } from "@/components/layout/breadcrumbs";
import { cn } from "@/lib/utils";

type AnalyticsHeaderProps = {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: ReactNode;
  className?: string;
};

export function AnalyticsHeader({
  title,
  description,
  breadcrumbs,
  actions,
  className,
}: AnalyticsHeaderProps) {
  return (
    <PageHeader
      className={className}
      title={title}
      description={description}
      breadcrumbs={
        breadcrumbs?.length ? <Breadcrumbs items={breadcrumbs} /> : undefined
      }
      actions={actions}
    />
  );
}

type AnalyticsToolbarProps = {
  leading?: ReactNode;
  trailing?: ReactNode;
  className?: string;
};

export function AnalyticsToolbar({ leading, trailing, className }: AnalyticsToolbarProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-lg border border-border bg-card p-3 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
      role="toolbar"
      aria-label="Analytics toolbar"
    >
      <div className="flex min-w-0 flex-wrap items-center gap-2">{leading}</div>
      <div className="flex flex-wrap items-center gap-2">{trailing}</div>
    </div>
  );
}

type AnalyticsFooterProps = {
  children?: ReactNode;
  className?: string;
};

export function AnalyticsFooter({ children, className }: AnalyticsFooterProps) {
  return (
    <footer
      className={cn(
        "flex flex-col gap-2 border-t border-border pt-4 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      {children ?? <p>Analytics module · read-only insights</p>}
    </footer>
  );
}

type AnalyticsPageLayoutProps = {
  header: ReactNode;
  toolbar?: ReactNode;
  filters?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
};

/**
 * Standard composition shell for future analytics feature pages.
 */
export function AnalyticsPageLayout({
  header,
  toolbar,
  filters,
  children,
  footer,
  className,
}: AnalyticsPageLayoutProps) {
  return (
    <div className={cn("flex flex-col gap-6", className)}>
      {header}
      {toolbar}
      {filters}
      <div className="flex flex-col gap-8">{children}</div>
      {footer}
    </div>
  );
}
