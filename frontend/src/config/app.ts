/**
 * Public frontend configuration.
 * Values come from NEXT_PUBLIC_* env vars — no secrets here.
 */
function readPublic(name: string, fallback?: string): string | undefined {
  const value = process.env[name];
  if (value === undefined || value === "") return fallback;
  return value;
}

export const appConfig = {
  appName:
    readPublic("NEXT_PUBLIC_APP_NAME") ?? "Enterprise Decision Platform",
  apiBaseUrl:
    readPublic("NEXT_PUBLIC_API_BASE_URL") ??
    readPublic("NEXT_PUBLIC_API_URL") ??
    "http://localhost:8000",
  environment:
    readPublic("NEXT_PUBLIC_ENVIRONMENT") ??
    readPublic("NEXT_PUBLIC_APP_ENV") ??
    "development",
  enableAnalytics: (readPublic("NEXT_PUBLIC_ENABLE_ANALYTICS") ?? "true") === "true",
  authRequired: (readPublic("NEXT_PUBLIC_AUTH_REQUIRED") ?? "false") === "true",
} as const;
