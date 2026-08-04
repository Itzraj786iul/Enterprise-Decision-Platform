/**
 * Cross-package TypeScript contracts shared by frontend (and future packages).
 * Keep this package free of runtime framework imports.
 */

export type HealthStatus = "ok" | "degraded" | "error";

export interface HealthPayload {
  status: HealthStatus;
  service: string;
  timestamp: string;
}
