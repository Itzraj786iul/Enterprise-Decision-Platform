"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { useThemePreferenceStore } from "@/store/theme-store";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const setPreference = useThemePreferenceStore((s) => s.setPreference);
  const isDark = resolvedTheme === "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      className="relative"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => {
        const next = isDark ? "light" : "dark";
        setPreference(next);
        setTheme(next);
      }}
    >
      <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
