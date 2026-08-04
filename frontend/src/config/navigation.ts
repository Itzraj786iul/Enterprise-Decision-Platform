import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Brain,
  Building2,
  CircleHelp,
  FileText,
  Handshake,
  Info,
  LayoutDashboard,
  Package,
  Settings,
  ShoppingCart,
  Sparkles,
  Users,
  Wallet,
} from "lucide-react";

export type NavBadge = {
  label: string;
  tone?: "default" | "success" | "warning" | "danger" | "info" | "muted";
};

export type NavItem = {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: NavBadge;
  children?: NavItem[];
  keywords?: string[];
  /** When true, item is shown but not navigable (unavailable feature). */
  disabled?: boolean;
};

export type NavSection = {
  id: string;
  label: string;
  items: NavItem[];
};

export const workspaces = [
  { id: "enterprise", label: "Enterprise HQ" },
  { id: "retail-us", label: "Retail — US" },
  { id: "sandbox", label: "Sandbox" },
] as const;

export type WorkspaceId = (typeof workspaces)[number]["id"];

export const navigationSections: NavSection[] = [
  {
    id: "main",
    label: "Main",
    items: [
      {
        id: "dashboard",
        label: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
        keywords: ["home", "overview"],
      },
      {
        id: "sales",
        label: "Sales Intelligence",
        href: "/sales",
        icon: ShoppingCart,
        keywords: ["revenue", "orders"],
      },
      {
        id: "customers",
        label: "Customer Intelligence",
        href: "/customers",
        icon: Users,
        keywords: ["segment", "churn"],
      },
      {
        id: "finance",
        label: "Finance Intelligence",
        href: "/finance",
        icon: Wallet,
        keywords: ["margin", "profit"],
      },
      {
        id: "operations",
        label: "Operations Intelligence",
        href: "/operations",
        icon: Package,
        keywords: ["inventory", "fulfillment"],
      },
      {
        id: "analytics",
        label: "Analytics",
        href: "/analytics",
        icon: BarChart3,
        keywords: ["explore", "insights"],
      },
      {
        id: "predictions",
        label: "AI Predictions",
        href: "/predictions",
        icon: Brain,
        keywords: ["ml", "forecast", "models"],
      },
      {
        id: "recommendations",
        label: "Business Recommendations",
        href: "/recommendations",
        icon: Sparkles,
        keywords: ["decisions", "actions"],
      },
      {
        id: "reports",
        label: "Reports",
        href: "/reports",
        icon: FileText,
        keywords: ["export", "pdf"],
      },
    ],
  },
  {
    id: "system",
    label: "System",
    items: [
      {
        id: "settings",
        label: "Settings",
        href: "/settings",
        icon: Settings,
        keywords: ["preferences", "profile"],
        children: [
          {
            id: "settings-general",
            label: "General",
            href: "/settings",
            icon: Settings,
            keywords: ["preferences"],
          },
          {
            id: "settings-help",
            label: "Help center",
            href: "/help",
            icon: CircleHelp,
            keywords: ["docs"],
          },
        ],
      },
      {
        id: "help",
        label: "Help",
        href: "/help",
        icon: CircleHelp,
        keywords: ["docs", "guide"],
      },
      {
        id: "about",
        label: "About",
        href: "/about",
        icon: Info,
        keywords: ["version"],
      },
      {
        id: "support",
        label: "Support",
        href: "/support",
        icon: Handshake,
        keywords: ["contact"],
      },
    ],
  },
];

export function flattenNavItems(sections: NavSection[] = navigationSections): NavItem[] {
  const result: NavItem[] = [];
  const walk = (items: NavItem[]) => {
    for (const item of items) {
      result.push(item);
      if (item.children?.length) walk(item.children);
    }
  };
  for (const section of sections) walk(section.items);
  return result;
}

export function findNavItemByHref(pathname: string): NavItem | undefined {
  const items = flattenNavItems();
  const exact = items.find((item) => item.href === pathname);
  if (exact) return exact;
  return items
    .filter((item) => item.href !== "/" && pathname.startsWith(`${item.href}/`))
    .sort((a, b) => b.href.length - a.href.length)[0];
}

export function buildBreadcrumbs(pathname: string): { label: string; href?: string }[] {
  if (pathname === "/") {
    return [{ label: "Home" }];
  }

  const crumbs: { label: string; href?: string }[] = [{ label: "Home", href: "/" }];
  const segments = pathname.split("/").filter(Boolean);
  let acc = "";

  for (const segment of segments) {
    acc += `/${segment}`;
    const match = findNavItemByHref(acc) ?? flattenNavItems().find((i) => i.href === acc);
    crumbs.push({
      label:
        match?.label ??
        segment.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      href: acc,
    });
  }

  if (crumbs.length > 0) {
    const last = crumbs[crumbs.length - 1];
    crumbs[crumbs.length - 1] = { label: last.label };
  }

  return crumbs;
}

export const brand = {
  name: "Decision Platform",
  shortName: "EDP",
  icon: Building2,
} as const;

/** Suggested pages shown in global search (UI only). */
export const suggestedPages = flattenNavItems().slice(0, 6);
