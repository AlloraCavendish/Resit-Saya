// Purpose: Loading spinner component for asynchronous data retrieval states.
// Security: Pure presentational component; renders sanitized static SVG/CSS indicators.

import React from "react";
import "./LoadingSpinner.css";

export function LoadingSpinner({ message = "Loading..." }) {
  return (
    <div className="spinner-container" role="status" aria-live="polite">
      <div className="spinner-circle"></div>
      {message && <p className="spinner-text">{message}</p>}
    </div>
  );
}
