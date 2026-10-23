// Purpose: Administrative management API client methods.
// Security: Communicates with admin-gated routes; non-admin tokens receive 403.

import { request } from "./client";

export function getAdminDashboard() {
  return request("/admin/dashboard", { method: "GET" });
}

export function getAuditLogs(eventFilter = null) {
  const query = eventFilter ? `?event=${encodeURIComponent(eventFilter)}` : "";
  return request(`/admin/audit-log${query}`, { method: "GET" });
}

export function listAdminUsers() {
  return request("/admin/users", { method: "GET" });
}

export function createAdminUser(data) {
  return request("/admin/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateAdminUser(userId, data) {
  return request(`/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function resetUserPassword(userId, newPassword) {
  return request(`/admin/users/${userId}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  });
}
