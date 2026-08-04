"use client";

import * as React from "react";
import { CircleHelp, Handshake, Info } from "lucide-react";

import {
  canAccessFeature,
  featureRegistry,
  filterFeaturesByPermissions,
  type FeatureDefinition,
  type FeaturePermission,
} from "@/config/feature-registry";
import type { NavItem, NavSection } from "@/config/navigation";

/** Dev / demo roles map to permission sets until IdP is wired. */
const ROLE_PERMISSIONS: Record<string, FeaturePermission[]> = {
  admin: ["admin:all"],
  executive: [
    "dashboard:read",
    "sales:read",
    "customers:read",
    "finance:read",
    "operations:read",
    "analytics:read",
    "ml:read",
    "reports:read",
    "settings:read",
    "export:run",
  ],
  finance: [
    "dashboard:read",
    "finance:read",
    "analytics:read",
    "reports:read",
    "settings:read",
    "export:run",
  ],
  operations: [
    "dashboard:read",
    "operations:read",
    "analytics:read",
    "reports:read",
    "settings:read",
    "export:run",
  ],
  sales: [
    "dashboard:read",
    "sales:read",
    "customers:read",
    "analytics:read",
    "reports:read",
    "settings:read",
    "export:run",
  ],
  analyst: [
    "dashboard:read",
    "sales:read",
    "customers:read",
    "finance:read",
    "operations:read",
    "analytics:read",
    "ml:read",
    "reports:read",
    "settings:read",
    "export:run",
  ],
  viewer: [
    "dashboard:read",
    "sales:read",
    "customers:read",
    "finance:read",
    "operations:read",
    "analytics:read",
    "reports:read",
    "settings:read",
  ],
};

function permissionsForRoles(roles: string[]): string[] {
  const out = new Set<string>();
  for (const role of roles) {
    for (const p of ROLE_PERMISSIONS[role.toLowerCase()] ?? []) {
      out.add(p);
    }
  }
  return [...out];
}

function readDevRoles(): string[] {
  if (typeof window === "undefined") {
    return (process.env.NEXT_PUBLIC_DEV_ROLES ?? "admin")
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean);
  }
  const stored = window.localStorage.getItem("edp.roles");
  if (stored) {
    return stored.split(",").map((r) => r.trim()).filter(Boolean);
  }
  return (process.env.NEXT_PUBLIC_DEV_ROLES ?? "admin")
    .split(",")
    .map((r) => r.trim())
    .filter(Boolean);
}

export type AuthSession = {
  roles: string[];
  permissions: string[];
  isAuthenticated: boolean;
};

export function useAuthSession(): AuthSession {
  const [roles, setRoles] = React.useState<string[]>(() =>
    typeof window === "undefined" ? ["admin"] : readDevRoles(),
  );

  React.useEffect(() => {
    setRoles(readDevRoles());
  }, []);

  const permissions = React.useMemo(() => permissionsForRoles(roles), [roles]);

  return {
    roles,
    permissions,
    isAuthenticated: roles.length > 0,
  };
}

export function useVisibleFeatures(): FeatureDefinition[] {
  const { permissions } = useAuthSession();
  return React.useMemo(
    () => filterFeaturesByPermissions(permissions),
    [permissions],
  );
}

export function featureToNavItem(feature: FeatureDefinition): NavItem {
  return {
    id: feature.id,
    label: feature.navigationLabel,
    href: feature.route,
    icon: feature.icon,
    keywords: feature.keywords,
    disabled: !feature.available,
  };
}

const STATIC_SYSTEM_ITEMS: NavItem[] = [
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
];

export function usePermissionAwareNavigation(): NavSection[] {
  const features = useVisibleFeatures();

  return React.useMemo(() => {
    const main = features.filter((f) => f.section === "main").map(featureToNavItem);
    const system = [
      ...features.filter((f) => f.section === "system").map(featureToNavItem),
      ...STATIC_SYSTEM_ITEMS,
    ];
    const sections: NavSection[] = [];
    if (main.length) {
      sections.push({ id: "main", label: "Workspace", items: main });
    }
    if (system.length) {
      sections.push({ id: "system", label: "System", items: system });
    }
    return sections;
  }, [features]);
}

export function useCanAccessRoute(pathname: string): boolean {
  const { permissions } = useAuthSession();
  const feature = featureRegistry.find(
    (f) => pathname === f.route || pathname.startsWith(`${f.route}/`),
  );
  if (!feature) return true;
  return canAccessFeature(feature, permissions);
}
