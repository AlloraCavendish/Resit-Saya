// Purpose: Card component for displaying receipt details on mobile viewports.
// Security: Sanitizes user inputs, relies on safe link routing, avoids raw HTML injections.

import React from "react";
import { Link } from "react-router-dom";
import { formatRm } from "../utils/money";
import { formatDate } from "../utils/date";
import "./ReceiptCard.css";

export function ReceiptCard({ receipt, onDelete, onRestore, isTrash = false }) {
  const isSplit =
    receipt.receipt_total_sen &&
    receipt.receipt_total_sen > receipt.my_share_sen;

  return (
    <div className="receipt-card">
      <div className="receipt-card-header">
        <div className="receipt-card-merchant-wrap">
          <Link to={`/receipts/${receipt.id}`} className="receipt-card-merchant">
            {receipt.merchant}
          </Link>
          <span className="receipt-card-date">
            {formatDate(receipt.receipt_date)}
          </span>
        </div>
        <div className="receipt-card-amount-wrap">
          <span className="receipt-card-my-share">
            {formatRm(receipt.my_share_sen)}
          </span>
          {isSplit && (
            <span className="receipt-card-split-tag">
              Split of {formatRm(receipt.receipt_total_sen)}
            </span>
          )}
        </div>
      </div>

      <div className="receipt-card-body">
        {receipt.category_name && (
          <span className="receipt-badge category-badge">
            🏷️ {receipt.category_name}
          </span>
        )}
        {receipt.has_file && (
          <span className="receipt-badge file-badge">
            📎 Receipt attached
          </span>
        )}
        {receipt.shared_with && (
          <span className="receipt-shared">
            👥 {receipt.shared_with}
          </span>
        )}
      </div>

      {receipt.notes && (
        <p className="receipt-card-notes">{receipt.notes}</p>
      )}

      <div className="receipt-card-actions">
        {isTrash ? (
          <>
            {receipt.days_remaining !== undefined && (
              <span className="trash-days">
                ⏳ {receipt.days_remaining} {receipt.days_remaining === 1 ? "day" : "days"} left
              </span>
            )}
            <div className="receipt-card-btn-group">
              <button
                type="button"
                className="btn-secondary card-btn"
                onClick={() => onRestore && onRestore(receipt.id)}
              >
                Restore
              </button>
              <button
                type="button"
                className="btn-danger-outline card-btn"
                onClick={() => onDelete && onDelete(receipt.id)}
              >
                Delete permanently
              </button>
            </div>
          </>
        ) : (
          <div className="receipt-card-btn-group">
            <Link to={`/receipts/${receipt.id}`} className="card-link-btn">
              View details
            </Link>
            <Link to={`/receipts/${receipt.id}/edit`} className="card-link-btn secondary">
              Edit
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
