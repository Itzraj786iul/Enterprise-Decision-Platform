import { describe, expect, it } from "vitest";

import {
  canAccessFeature,
  featureRegistry,
  filterFeaturesByPermissions,
  getFeature,
  listAvailableFeatures,
} from "@/config/feature-registry";

describe("feature registry", () => {
  it("lists available core modules", () => {
    const ids = listAvailableFeatures().map((f) => f.id);
    expect(ids).toEqual(
      expect.arrayContaining(["dashboard", "sales", "customers", "finance", "operations", "settings"]),
    );
    expect(ids).not.toContain("predictions");
  });

  it("hides unavailable features by default", () => {
    const filtered = filterFeaturesByPermissions(["admin:all"]);
    expect(filtered.every((f) => f.available)).toBe(true);
    expect(getFeature("analytics")?.available).toBe(false);
  });

  it("filters by permission", () => {
    const financeOnly = filterFeaturesByPermissions(["finance:read", "dashboard:read", "settings:read"]);
    const ids = financeOnly.map((f) => f.id);
    expect(ids).toContain("finance");
    expect(ids).toContain("dashboard");
    expect(ids).not.toContain("sales");
  });

  it("admin can access any available feature", () => {
    const sales = getFeature("sales");
    expect(sales).toBeTruthy();
    expect(canAccessFeature(sales!, ["admin:all"])).toBe(true);
  });

  it("registry entries include nav metadata", () => {
    for (const feature of featureRegistry.filter((f) => f.available)) {
      expect(feature.route).toMatch(/^\//);
      expect(feature.navigationLabel.length).toBeGreaterThan(0);
      expect(feature.permissions.length).toBeGreaterThan(0);
    }
  });
});
