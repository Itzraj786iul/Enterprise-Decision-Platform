"use client";

import { motion } from "framer-motion";
import { AppShell } from "@/components/layout/app-shell";
import { ContentContainer } from "@/components/layout/content-container";
import { useShellStore } from "@/store/shell-store";
import { useShellShortcuts } from "@/hooks/use-shell-shortcuts";
import { AppSidebar } from "@/components/shell/app-sidebar";
import { AppTopNav } from "@/components/shell/app-top-nav";
import { MobileNavDrawer } from "@/components/shell/mobile-nav-drawer";
import { CommandPalette } from "@/components/shell/command-palette";
import { GlobalSearch } from "@/components/shell/global-search";

type ApplicationShellProps = {
  children: React.ReactNode;
};

/**
 * Full enterprise application framework shell.
 * No analytics, dashboards, or API data — chrome only.
 */
export function ApplicationShell({ children }: ApplicationShellProps) {
  const sidebarCollapsed = useShellStore((s) => s.sidebarCollapsed);
  useShellShortcuts();

  return (
    <>
      <AppShell
        sidebarCollapsed={sidebarCollapsed}
        sidebar={
          <motion.div
            className="h-full"
            animate={{ width: "100%" }}
            transition={{ duration: 0.2 }}
          >
            <AppSidebar />
          </motion.div>
        }
        navbar={<AppTopNav />}
      >
        <ContentContainer className="min-h-[calc(100vh-3.5rem)]">{children}</ContentContainer>
      </AppShell>
      <MobileNavDrawer />
      <CommandPalette />
      <GlobalSearch />
    </>
  );
}
