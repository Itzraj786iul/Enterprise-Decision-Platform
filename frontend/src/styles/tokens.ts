/**
 * Enterprise Decision Platform — Design Tokens
 * Source of truth for spacing, radius, shadow, motion, and layout.
 * Colors live in CSS variables (globals.css) for light/dark themes.
 */

export const typography = {
  fontFamily: {
    sans: "var(--font-sans)",
    mono: "var(--font-mono)",
    display: "var(--font-display)",
  },
  fontSize: {
    xs: "0.75rem",
    sm: "0.875rem",
    base: "1rem",
    lg: "1.125rem",
    xl: "1.25rem",
    "2xl": "1.5rem",
    "3xl": "1.875rem",
    "4xl": "2.25rem",
  },
  fontWeight: {
    normal: "400",
    medium: "500",
    semibold: "600",
    bold: "700",
  },
  lineHeight: {
    tight: "1.25",
    snug: "1.375",
    normal: "1.5",
    relaxed: "1.625",
  },
  letterSpacing: {
    tight: "-0.025em",
    normal: "0",
    wide: "0.025em",
  },
} as const;

export const spacing = {
  0: "0",
  px: "1px",
  0.5: "0.125rem",
  1: "0.25rem",
  1.5: "0.375rem",
  2: "0.5rem",
  2.5: "0.625rem",
  3: "0.75rem",
  4: "1rem",
  5: "1.25rem",
  6: "1.5rem",
  8: "2rem",
  10: "2.5rem",
  12: "3rem",
  16: "4rem",
  20: "5rem",
  24: "6rem",
} as const;

export const radius = {
  none: "0",
  sm: "0.25rem",
  md: "0.375rem",
  lg: "0.5rem",
  xl: "0.75rem",
  "2xl": "1rem",
  full: "9999px",
} as const;

export const shadow = {
  xs: "var(--shadow-xs)",
  sm: "var(--shadow-sm)",
  md: "var(--shadow-md)",
  lg: "var(--shadow-lg)",
  focus: "var(--shadow-focus)",
} as const;

export const motion = {
  duration: {
    instant: "0ms",
    fast: "120ms",
    normal: "200ms",
    slow: "320ms",
    slower: "480ms",
  },
  easing: {
    standard: "cubic-bezier(0.2, 0, 0, 1)",
    emphasized: "cubic-bezier(0.2, 0, 0, 1)",
    enter: "cubic-bezier(0, 0, 0.2, 1)",
    exit: "cubic-bezier(0.4, 0, 1, 1)",
  },
} as const;

export const layout = {
  sidebarWidth: "16rem",
  sidebarCollapsedWidth: "4.5rem",
  topNavbarHeight: "3.5rem",
  contentMaxWidth: "90rem",
  container: {
    sm: "40rem",
    md: "48rem",
    lg: "64rem",
    xl: "80rem",
    "2xl": "90rem",
  },
  breakpoints: {
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },
  grid: {
    columns: 12,
    gutter: "1.5rem",
  },
} as const;

export const zIndex = {
  base: 0,
  sticky: 20,
  dropdown: 40,
  overlay: 50,
  modal: 60,
  toast: 70,
  tooltip: 80,
} as const;

export type SemanticColor =
  | "primary"
  | "secondary"
  | "accent"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

export type TrendDirection = "up" | "down" | "flat";
