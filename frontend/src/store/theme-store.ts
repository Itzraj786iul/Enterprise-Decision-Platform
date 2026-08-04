"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

type ThemePreference = "light" | "dark" | "system";

type ThemeState = {
  preference: ThemePreference;
  setPreference: (preference: ThemePreference) => void;
};

/**
 * Persists theme preference alongside next-themes.
 * next-themes remains the runtime source of truth for class application.
 */
export const useThemePreferenceStore = create<ThemeState>()(
  persist(
    (set) => ({
      preference: "system",
      setPreference: (preference) => set({ preference }),
    }),
    {
      name: "edp-theme",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
