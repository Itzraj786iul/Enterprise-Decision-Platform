"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { WorkspaceId } from "@/config/navigation";

type ShellState = {
  sidebarCollapsed: boolean;
  mobileNavOpen: boolean;
  commandPaletteOpen: boolean;
  globalSearchOpen: boolean;
  workspaceId: WorkspaceId;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebarCollapsed: () => void;
  setMobileNavOpen: (open: boolean) => void;
  toggleMobileNav: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setGlobalSearchOpen: (open: boolean) => void;
  setWorkspaceId: (id: WorkspaceId) => void;
};

export const useShellStore = create<ShellState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      mobileNavOpen: false,
      commandPaletteOpen: false,
      globalSearchOpen: false,
      workspaceId: "enterprise",
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      toggleSidebarCollapsed: () =>
        set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setMobileNavOpen: (open) => set({ mobileNavOpen: open }),
      toggleMobileNav: () => set((s) => ({ mobileNavOpen: !s.mobileNavOpen })),
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
      setGlobalSearchOpen: (open) => set({ globalSearchOpen: open }),
      setWorkspaceId: (id) => set({ workspaceId: id }),
    }),
    {
      name: "edp-shell",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        workspaceId: state.workspaceId,
      }),
    },
  ),
);

/** @deprecated Prefer useShellStore — kept for compatibility */
export const useUiStore = useShellStore;
