/**
 * Central frontend feature registry — mirrors backend platform registry.
 */

import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Brain,
  FileText,
  LayoutDashboard,
  Package,
  Settings,
  ShoppingCart,
  Sparkles,
  Users,
  Wallet,
} from "lucide-react";

export type FeaturePermission =
  | "dashboard:read"
  | "sales:read"
  | "customers:read"
  | "finance:read"
  | "operations:read"
  | "analytics:read"
  | "ml:read"
  | "reports:read"
  | "settings:read"
  | "settings:write"
  | "export:run"
  | "admin:all";

export type FeatureFilterKey =
  | "date"
  | "region"
  | "category"
  | "customer"
  | "product"
  | "segment"
  | "department"
  | "supplier"
  | "search";

export type FeatureDefinition = {
  id: string;
  route: string;
  apiPrefix?: string;
  navigationLabel: string;
  icon: LucideIcon;
  permissions: FeaturePermission[];
  supportedFilters: FeatureFilterKey[];
  exportSupport: boolean;
  available: boolean;
  section: "main" | "system";
  description?: string;
  keywords?: string[];
};

export const featureRegistry: FeatureDefinition[] = [
  {
    id: "dashboard",
    route: "/dashboard",
    apiPrefix: "/api/v1/dashboard",
    navigationLabel: "Dashboard",
    icon: LayoutDashboard,
    permissions: ["dashboard:read"],
    supportedFilters: ["date"],
    exportSupport: false,
    available: true,
    section: "main",
    keywords: ["home", "overview"],
  },
  {
    id: "sales",
    route: "/sales",
    apiPrefix: "/api/v1/sales",
    navigationLabel: "Sales Intelligence",
    icon: ShoppingCart,
    permissions: ["sales:read"],
    supportedFilters: ["date", "region", "category", "search"],
    exportSupport: true,
    available: true,
    section: "main",
    keywords: ["revenue", "orders"],
  },
  {
    id: "customers",
    route: "/customers",
    apiPrefix: "/api/v1/customers",
    navigationLabel: "Customer Intelligence",
    icon: Users,
    permissions: ["customers:read"],
    supportedFilters: ["date", "region", "segment", "search"],
    exportSupport: true,
    available: true,
    section: "main",
    keywords: ["segment", "churn"],
  },
  {
    id: "finance",
    route: "/finance",
    apiPrefix: "/api/v1/finance",
    navigationLabel: "Finance Intelligence",
    icon: Wallet,
    permissions: ["finance:read"],
    supportedFilters: ["date", "region", "department", "category", "search"],
    exportSupport: true,
    available: true,
    section: "main",
    keywords: ["margin", "profit"],
  },
  {
    id: "operations",
    route: "/operations",
    apiPrefix: "/api/v1/operations",
    navigationLabel: "Operations Intelligence",
    icon: Package,
    permissions: ["operations:read"],
    supportedFilters: ["date", "region", "category", "supplier", "search"],
    exportSupport: true,
    available: true,
    section: "main",
    keywords: ["inventory", "fulfillment"],
  },
  {
    id: "analytics",
    route: "/analytics",
    navigationLabel: "Analytics",
    icon: BarChart3,
    permissions: ["analytics:read"],
    supportedFilters: ["date", "search"],
    exportSupport: false,
    available: false,
    section: "main",
    keywords: ["explore", "insights"],
  },
  {
    id: "predictions",
    route: "/predictions",
    navigationLabel: "AI Predictions",
    icon: Brain,
    permissions: ["ml:read"],
    supportedFilters: ["date", "search"],
    exportSupport: false,
    available: false,
    section: "main",
    keywords: ["ml", "forecast", "models"],
  },
  {
    id: "recommendations",
    route: "/recommendations",
    navigationLabel: "Business Recommendations",
    icon: Sparkles,
    permissions: ["analytics:read"],
    supportedFilters: [],
    exportSupport: false,
    available: false,
    section: "main",
    keywords: ["decisions", "actions"],
  },
  {
    id: "reports",
    route: "/reports",
    navigationLabel: "Reports",
    icon: FileText,
    permissions: ["reports:read"],
    supportedFilters: [],
    exportSupport: true,
    available: false,
    section: "main",
    keywords: ["export", "pdf"],
  },
  {
    id: "settings",
    route: "/settings",
    navigationLabel: "Settings",
    icon: Settings,
    permissions: ["settings:read"],
    supportedFilters: [],
    exportSupport: false,
    available: true,
    section: "system",
    keywords: ["preferences", "profile"],
  },
];

export function listAvailableFeatures(): FeatureDefinition[] {
  return featureRegistry.filter((f) => f.available);
}

export function getFeature(id: string): FeatureDefinition | undefined {
  return featureRegistry.find((f) => f.id === id);
}

export function canAccessFeature(
  feature: FeatureDefinition,
  permissions: readonly string[],
): boolean {
  if (!feature.available) return false;
  if (permissions.includes("admin:all")) return true;
  if (feature.permissions.length === 0) return true;
  return feature.permissions.some((p) => permissions.includes(p));
}

export function filterFeaturesByPermissions(
  permissions: readonly string[],
  options: { includeUnavailable?: boolean } = {},
): FeatureDefinition[] {
  const includeUnavailable = options.includeUnavailable ?? false;
  return featureRegistry.filter((feature) => {
    if (!includeUnavailable && !feature.available) return false;
    if (!feature.available && includeUnavailable) {
      return permissions.includes("admin:all")
        || feature.permissions.some((p) => permissions.includes(p));
    }
    return canAccessFeature(feature, permissions);
  });
}
