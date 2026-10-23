// Purpose: Receipts management API client methods.
// Security: Communicates with receipt endpoints, file uploads, soft-deletion, and restoration.

import { request } from "./client";

export function getReceipts({ search, startDate, endDate, categoryId, page = 1, pageSize = 20 } = {}) {
  const params = new URLSearchParams();
  if (search) params.append("search", search);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);
  if (categoryId) params.append("category_id", categoryId);
  params.append("page", page);
  params.append("page_size", pageSize);

  return request(`/receipts?${params.toString()}`, { method: "GET" });
}

export function getReceipt(id) {
  return request(`/receipts/${id}`, { method: "GET" });
}

export function createReceipt(data) {
  return request("/receipts", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateReceipt(id, data) {
  return request(`/receipts/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteReceipt(id) {
  return request(`/receipts/${id}`, {
    method: "DELETE",
  });
}

export function getTrash() {
  return request("/receipts/trash", { method: "GET" });
}

export function restoreReceipt(id) {
  return request(`/receipts/${id}/restore`, {
    method: "POST",
  });
}

export function permanentDeleteReceipt(id) {
  return request(`/receipts/${id}/permanent`, {
    method: "DELETE",
  });
}

export function uploadReceiptFile(id, file) {
  const formData = new FormData();
  formData.append("file", file);
  return request(`/receipts/${id}/file`, {
    method: "POST",
    body: formData,
  });
}

export function deleteReceiptFile(id) {
  return request(`/receipts/${id}/file`, {
    method: "DELETE",
  });
}

export function getReceiptFileUrl(id) {
  return `/api/receipts/${id}/file`;
}
