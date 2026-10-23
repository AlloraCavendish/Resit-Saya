// Purpose: Public metadata and server time synchronization API methods.
// Security: Accesses unauthenticated status endpoints.

import { request } from "./client";

export function getServerTime() {
  return request("/time", { method: "GET" });
}

export function getHealth() {
  return request("/health", { method: "GET" });
}
