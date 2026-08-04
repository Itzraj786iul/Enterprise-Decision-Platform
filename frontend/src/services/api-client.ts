import { appConfig } from "@/config/app";

const ACCESS_TOKEN_KEY = "edp.access_token";

function readBearerToken(): string | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    return window.localStorage.getItem(ACCESS_TOKEN_KEY) ?? undefined;
  } catch {
    return undefined;
  }
}

/**
 * Thin HTTP client for the FastAPI backend.
 * Attaches Bearer JWT from localStorage when present (IdP-ready; no UI change).
 */
export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${appConfig.apiBaseUrl}${path}`;
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = readBearerToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}
