/** Shared frontend TypeScript types (domain types added later). */

export type ApiHealthResponse = {
  status: string;
  service: string;
  timestamp: string;
};

export type PlaceholderResponse = {
  status: string;
  message: string;
  resource: string;
};
