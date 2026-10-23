// Purpose: Error alert component displaying user-facing error feedback.
// Security: Sanitizes user error messages; renders strings safely as text nodes without innerHTML.

import React from "react";
import "./ErrorMessage.css";

export function ErrorMessage({ message, onRetry }) {
  if (!message) return null;

  return (
    <div className="error-banner" role="alert">
      <div className="error-icon" aria-hidden="true">⚠️</div>
      <div className="error-content">
        <p className="error-text">{message}</p>
        {onRetry && (
          <button type="button" onClick={onRetry} className="error-retry-btn">
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
