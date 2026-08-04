"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { FileText, LayoutGrid, Settings, Sparkles, type LucideIcon } from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { flattenNavItems } from "@/config/navigation";
import { usePermissionAwareNavigation } from "@/hooks/use-auth-session";
import { useShellStore } from "@/store/shell-store";
import { useThemePreferenceStore } from "@/store/theme-store";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

type ActionItem = {
  id: string;
  label: string;
  keywords?: string;
  icon: LucideIcon;
  run: () => void;
};

export function CommandPalette() {
  const router = useRouter();
  const open = useShellStore((s) => s.commandPaletteOpen);
  const setOpen = useShellStore((s) => s.setCommandPaletteOpen);
  const setGlobalSearchOpen = useShellStore((s) => s.setGlobalSearchOpen);
  const toggleSidebarCollapsed = useShellStore((s) => s.toggleSidebarCollapsed);
  const setPreference = useThemePreferenceStore((s) => s.setPreference);
  const { setTheme } = useTheme();

  const sections = usePermissionAwareNavigation();
  const pages = React.useMemo(() => flattenNavItems(sections), [sections]);

  const actions: ActionItem[] = [
    {
      id: "open-search",
      label: "Open global search",
      icon: LayoutGrid,
      keywords: "find",
      run: () => {
        setOpen(false);
        setGlobalSearchOpen(true);
      },
    },
    {
      id: "toggle-sidebar",
      label: "Toggle sidebar",
      icon: LayoutGrid,
      run: () => toggleSidebarCollapsed(),
    },
    {
      id: "theme-light",
      label: "Switch to light theme",
      icon: Sparkles,
      run: () => {
        setPreference("light");
        setTheme("light");
      },
    },
    {
      id: "theme-dark",
      label: "Switch to dark theme",
      icon: Sparkles,
      run: () => {
        setPreference("dark");
        setTheme("dark");
      },
    },
    {
      id: "theme-system",
      label: "Use system theme",
      icon: Sparkles,
      run: () => {
        setPreference("system");
        setTheme("system");
      },
    },
    {
      id: "go-settings",
      label: "Open settings",
      icon: Settings,
      run: () => router.push("/settings"),
    },
    {
      id: "go-reports",
      label: "Open reports",
      icon: FileText,
      run: () => router.push("/reports"),
    },
  ];

  React.useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(!open);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, setOpen]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="top-[18%] max-w-xl translate-y-0 overflow-hidden p-0">
        <DialogTitle className="sr-only">Command palette</DialogTitle>
        <Command className="bg-card text-card-foreground" loop>
          <div className="flex items-center border-b border-border px-3">
            <Command.Input
              placeholder="Type a command or search…"
              className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              aria-label="Command palette search"
            />
            <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
              ⌘K
            </kbd>
          </div>
          <Command.List className="max-h-80 overflow-auto p-2">
            <Command.Empty className="py-8 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>

            <Command.Group heading="Pages" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
              {pages.map((page) => {
                const Icon = page.icon;
                return (
                  <Command.Item
                    key={page.id}
                    value={`${page.label} ${page.keywords?.join(" ") ?? ""} page`}
                    onSelect={() => {
                      setOpen(false);
                      router.push(page.href);
                    }}
                    className={cn(
                      "flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-sm aria-selected:bg-muted",
                    )}
                  >
                    <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                    {page.label}
                  </Command.Item>
                );
              })}
            </Command.Group>

            <Command.Group heading="Actions" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
              {actions.map((action) => {
                const Icon = action.icon;
                return (
                  <Command.Item
                    key={action.id}
                    value={`${action.label} ${action.keywords ?? ""} action`}
                    onSelect={() => {
                      setOpen(false);
                      action.run();
                    }}
                    className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-sm aria-selected:bg-muted"
                  >
                    <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                    {action.label}
                  </Command.Item>
                );
              })}
            </Command.Group>

            <Command.Group heading="Reports & settings" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
              <Command.Item
                value="reports export"
                onSelect={() => {
                  setOpen(false);
                  router.push("/reports");
                }}
                className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-sm aria-selected:bg-muted"
              >
                <FileText className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                Browse reports
              </Command.Item>
              <Command.Item
                value="settings preferences"
                onSelect={() => {
                  setOpen(false);
                  router.push("/settings");
                }}
                className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-sm aria-selected:bg-muted"
              >
                <Settings className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                Platform settings
              </Command.Item>
            </Command.Group>

            <Command.Group heading="Coming soon" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
              <Command.Item
                value="customers products entities"
                disabled
                className="flex items-center gap-2 rounded-md px-2 py-2 text-sm text-muted-foreground opacity-60"
              >
                Search customers & products (future)
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
