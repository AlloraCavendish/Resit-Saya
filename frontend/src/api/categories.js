// Purpose: Categories management API client methods.
// Security: Communicates with user-scoped category endpoints.

import { request } from "./client";

export function getCategories() {
  return request("/categories", { method: "GET" });
}

export function createCategory(name) {
  return request("/categories", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function updateCategory(id, name) {
  return request(`/categories/${id}`, {
    method: "PUT",
    body: JSON.stringify({ name }),
  });
}

export function deleteCategory(id) {
  return request(`/categories/${id}`, {
    method: "DELETE",
  });
}
