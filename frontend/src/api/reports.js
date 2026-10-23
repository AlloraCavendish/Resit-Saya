// Purpose: Monthly expense reporting API client methods.
// Security: Requests aggregated financial calculations for the authenticated user.

import { request } from "./client";

export function getMonthlyReport(month) {
  const query = month ? `?month=${encodeURIComponent(month)}` : "";
  return request(`/reports/monthly${query}`, { method: "GET" });
}
