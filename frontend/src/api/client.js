// Purpose: Central HTTP client wrapper for API requests.
// Security: Enforces credentials: 'include' for HttpOnly session cookie handling; parses error messages safely.

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function request(endpoint, options = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `/api${endpoint}`;

  const config = {
    ...options,
    credentials: "include", // Essential for HttpOnly session cookies
    headers: {
      ...options.headers,
    },
  };

  // If payload is not FormData, default to application/json
  if (config.body && !(config.body instanceof FormData)) {
    if (!config.headers["Content-Type"]) {
      config.headers["Content-Type"] = "application/json";
    }
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch (err) {
    throw new ApiError(
      "Network connection error. Please check your connection.",
      0,
      null
    );
  }

  if (!response.ok) {
    let errorDetail = `Request failed (${response.status})`;
    let errorData = null;

    try {
      errorData = await response.json();
      if (errorData && errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          errorDetail = errorData.detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
        } else {
          errorDetail = String(errorData.detail);
        }
      }
    } catch {
      // Non-JSON response
    }

    throw new ApiError(errorDetail, response.status, errorData);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return await response.json();
  }

  return await response.text();
}
