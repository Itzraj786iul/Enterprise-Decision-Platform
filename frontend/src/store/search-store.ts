"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

type SearchState = {
  recentSearches: string[];
  addRecentSearch: (query: string) => void;
  clearRecentSearches: () => void;
  removeRecentSearch: (query: string) => void;
};

const MAX_RECENT = 8;

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      recentSearches: [],
      addRecentSearch: (query) => {
        const trimmed = query.trim();
        if (!trimmed) return;
        set((state) => ({
          recentSearches: [
            trimmed,
            ...state.recentSearches.filter((q) => q.toLowerCase() !== trimmed.toLowerCase()),
          ].slice(0, MAX_RECENT),
        }));
      },
      clearRecentSearches: () => set({ recentSearches: [] }),
      removeRecentSearch: (query) =>
        set((state) => ({
          recentSearches: state.recentSearches.filter((q) => q !== query),
        })),
    }),
    {
      name: "edp-search",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
