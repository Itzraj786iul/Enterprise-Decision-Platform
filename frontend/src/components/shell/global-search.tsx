"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Clock3, CornerDownLeft, Search, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { flattenNavItems } from "@/config/navigation";
import { usePermissionAwareNavigation } from "@/hooks/use-auth-session";
import { useSearchStore } from "@/store/search-store";
import { useShellStore } from "@/store/shell-store";
import { cn } from "@/lib/utils";

export function GlobalSearch() {
  const router = useRouter();
  const open = useShellStore((s) => s.globalSearchOpen);
  const setOpen = useShellStore((s) => s.setGlobalSearchOpen);
  const recentSearches = useSearchStore((s) => s.recentSearches);
  const addRecentSearch = useSearchStore((s) => s.addRecentSearch);
  const clearRecentSearches = useSearchStore((s) => s.clearRecentSearches);
  const removeRecentSearch = useSearchStore((s) => s.removeRecentSearch);
  const sections = usePermissionAwareNavigation();
  const pages = React.useMemo(() => flattenNavItems(sections), [sections]);
  const suggested = React.useMemo(() => pages.slice(0, 6), [pages]);

  const [query, setQuery] = React.useState("");
  const [activeIndex, setActiveIndex] = React.useState(0);
  const results = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return suggested;
    return pages.filter((item) => {
      const hay = `${item.label} ${item.href} ${(item.keywords ?? []).join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [query, pages, suggested]);

  React.useEffect(() => {
    if (!open) {
      setQuery("");
      setActiveIndex(0);
    }
  }, [open]);

  React.useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  const go = (href: string, label?: string) => {
    if (query.trim()) addRecentSearch(query);
    else if (label) addRecentSearch(label);
    setOpen(false);
    router.push(href);
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, Math.max(results.length - 1, 0)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter" && results[activeIndex]) {
      event.preventDefault();
      go(results[activeIndex].href, results[activeIndex].label);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent
        className="top-[20%] max-w-xl translate-y-0 gap-0 overflow-hidden p-0"
        onKeyDown={onKeyDown}
      >
        <DialogTitle className="sr-only">Global search</DialogTitle>
        <div className="flex items-center gap-2 border-b border-border px-3">
          <Search className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search pages…"
            className="h-12 border-0 shadow-none focus-visible:ring-0"
            aria-label="Search pages"
            autoFocus
          />
          <kbd className="hidden rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline">
            Esc
          </kbd>
        </div>

        <div className="max-h-80 overflow-auto p-2">
          {!query && recentSearches.length > 0 ? (
            <div className="mb-3">
              <div className="mb-1 flex items-center justify-between px-2">
                <p className="text-xs font-medium text-muted-foreground">Recent</p>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={clearRecentSearches}
                >
                  Clear
                </Button>
              </div>
              <ul className="space-y-0.5" role="list">
                {recentSearches.map((item) => (
                  <li key={item}>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm hover:bg-muted"
                      onClick={() => setQuery(item)}
                    >
                      <Clock3 className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
                      <span className="flex-1 truncate">{item}</span>
                      <span
                        className="rounded p-1 text-muted-foreground hover:bg-background"
                        role="presentation"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeRecentSearch(item);
                        }}
                      >
                        <X className="h-3 w-3" />
                        <span className="sr-only">Remove</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <p className="mb-1 px-2 text-xs font-medium text-muted-foreground">
            {query ? "Results" : "Suggested pages"}
          </p>
          <AnimatePresence initial={false} mode="popLayout">
            {results.length === 0 ? (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="px-2 py-6 text-center text-sm text-muted-foreground"
              >
                No matching pages. Try another term.
              </motion.p>
            ) : (
              <ul className="space-y-0.5" role="listbox" aria-label="Search results">
                {results.map((item, index) => {
                  const Icon = item.icon;
                  const selected = index === activeIndex;
                  return (
                    <li key={item.id} role="option" aria-selected={selected}>
                      <button
                        type="button"
                        className={cn(
                          "flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm",
                          selected ? "bg-muted" : "hover:bg-muted/70",
                        )}
                        onMouseEnter={() => setActiveIndex(index)}
                        onClick={() => go(item.href, item.label)}
                      >
                        <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                        <span className="flex-1 truncate font-medium">{item.label}</span>
                        <CornerDownLeft className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </AnimatePresence>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function GlobalSearchTrigger({ className }: { className?: string }) {
  const setOpen = useShellStore((s) => s.setGlobalSearchOpen);

  return (
    <Button
      type="button"
      variant="outline"
      className={cn(
        "relative h-9 w-full justify-start gap-2 text-sm text-muted-foreground sm:w-56 lg:w-72",
        className,
      )}
      onClick={() => setOpen(true)}
      aria-label="Open global search"
    >
      <Search className="h-4 w-4" aria-hidden="true" />
      <span className="truncate">Search…</span>
      <kbd className="pointer-events-none ml-auto hidden rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium sm:inline-block">
        /
      </kbd>
    </Button>
  );
}
