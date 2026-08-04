"use client";

import { usePathname, useRouter } from "next/navigation";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { TopNavbar } from "@/components/layout/top-navbar";
import { ThemeToggle } from "@/components/navigation/theme-toggle";
import { UserMenu } from "@/components/navigation/user-menu";
import { buildBreadcrumbs } from "@/config/navigation";
import { useShellStore } from "@/store/shell-store";
import { GlobalSearchTrigger } from "@/components/shell/global-search";
import { NotificationCenter } from "@/components/shell/notification-center";
import { WorkspaceSelector } from "@/components/shell/workspace-selector";

function CurrentDateLabel() {
  const label = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date());

  return (
    <time
      dateTime={new Date().toISOString().slice(0, 10)}
      className="hidden text-xs text-muted-foreground lg:inline"
    >
      {label}
    </time>
  );
}

export function AppTopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const setMobileNavOpen = useShellStore((s) => s.setMobileNavOpen);
  const crumbs = buildBreadcrumbs(pathname);

  return (
    <div className="space-y-0">
      <TopNavbar
        onMenuClick={() => setMobileNavOpen(true)}
        leading={
          <div className="hidden min-w-0 md:block">
            <Breadcrumbs items={crumbs} />
          </div>
        }
        trailing={
          <>
            <WorkspaceSelector />
            <CurrentDateLabel />
            <GlobalSearchTrigger className="hidden md:inline-flex" />
            <NotificationCenter />
            <ThemeToggle />
            <UserMenu
              name="Alex Morgan"
              email="alex.morgan@example.com"
              onProfile={() => router.push("/settings")}
              onSettings={() => router.push("/settings")}
              onSignOut={() => router.push("/")}
            />
          </>
        }
      />
      <div className="border-t border-border px-3 py-2 md:hidden">
        <Breadcrumbs items={crumbs} />
      </div>
      <div className="border-t border-border px-3 py-2 md:hidden">
        <GlobalSearchTrigger className="w-full" />
      </div>
    </div>
  );
}
