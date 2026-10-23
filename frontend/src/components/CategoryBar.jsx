// Purpose: Visual progress bar representing category expenditure share without chart libraries.
// Security: Sanitizes user labels; uses semantic HTML meter/progress elements.

import React from "react";
import "./CategoryBar.css";

export function CategoryBar({ name, amountFormatted, percentage, count }) {
  const safePercent = Math.min(100, Math.max(0, percentage || 0));

  return (
    <div className="cat-bar-item">
      <div className="cat-bar-info">
        <span className="cat-bar-name">{name}</span>
        <div className="cat-bar-figures">
          <span className="cat-bar-amount">{amountFormatted}</span>
          <span className="cat-bar-pct">({safePercent.toFixed(1)}%)</span>
        </div>
      </div>
      <div className="cat-bar-track">
        <progress
          className="cat-bar-progress"
          max="100"
          value={safePercent}
          aria-label={`${name}: ${safePercent.toFixed(1)} percent`}
        >
          {safePercent}%
        </progress>
      </div>
      {count !== undefined && (
        <span className="cat-bar-count">
          {count} {count === 1 ? "receipt" : "receipts"}
        </span>
      )}
    </div>
  );
}
