// Purpose: Authentication API client methods.
// Security: Communicates with cookie-based auth endpoints; handles logout and password changes.

import { request } from "./client";

export function login(username, password) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function logout() {
  return request("/auth/logout", {
    method: "POST",
  });
}

export function getMe() {
  return request("/auth/me", {
    method: "GET",
  });
}

export function changePassword(currentPassword, newPassword) {
  return request("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}
