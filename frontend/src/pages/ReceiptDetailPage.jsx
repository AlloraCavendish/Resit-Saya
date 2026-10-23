// Purpose: Receipt detail view displaying expense breakdown and embedded image/PDF document.
// Security: Requests file through authenticated proxy endpoint; escapes and validates all display data.

import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getReceipt, deleteReceipt, getReceiptFileUrl } from "../api/receipts";
import { formatRm } from "../utils/money";
import { formatDate } from "../utils/date";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import { ConfirmModal } from "../components/ConfirmModal";
import "./ReceiptDetailPage.css";

export function ReceiptDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [receipt, setReceipt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const fetchReceipt = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getReceipt(id);
      setReceipt(data);
    } catch (err) {
      setError(err.message || "Failed to load receipt details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReceipt();
  }, [id]);

  const handleDeleteConfirm = async () => {
    try {
      await deleteReceipt(id);
      navigate("/receipts");
    } catch (err) {
      setError(err.message || "Failed to delete receipt.");
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading receipt details..." />;
  }

  if (!receipt && error) {
    return (
      <div className="receipt-detail-page">
        <ErrorMessage message={error} />
        <Link to="/receipts" className="btn-secondary">
          ← Back to Receipts
        </Link>
      </div>
    );
  }

  const isSplit =
    receipt.receipt_total_sen &&
    receipt.receipt_total_sen > receipt.my_share_sen;
  const isPdf =
    receipt.original_filename &&
    receipt.original_filename.toLowerCase().endsWith(".pdf");
  const fileUrl = receipt.has_file ? getReceiptFileUrl(receipt.id) : null;

  return (
    <div className="receipt-detail-page">
      <div className="page-header">
        <div className="detail-header-left">
          <Link to="/receipts" className="detail-back-link">
            ← Back to Receipts
          </Link>
          <h1 className="page-title">{receipt.merchant}</h1>
          <span className="detail-date">{formatDate(receipt.receipt_date)}</span>
        </div>

        <div className="detail-actions">
          <Link to={`/receipts/${receipt.id}/edit`} className="btn-secondary detail-btn">
            ✏️ Edit
          </Link>
          <button
            type="button"
            className="btn-danger-outline detail-btn"
            onClick={() => setShowDeleteModal(true)}
          >
            🗑️ Move to Trash
          </button>
        </div>
      </div>

      <ErrorMessage message={error} />

      <div className="detail-content-grid">
        {/* Left Column: Financial & Meta Details */}
        <div className="card-surface detail-info-card">
          <h2 className="detail-section-title">Expense Breakdown</h2>

          <div className="detail-figures-box">
            <div className="figure-block my-share-figure">
              <span className="figure-label">MY SHARE</span>
              <span className="figure-value primary">{formatRm(receipt.my_share_sen)}</span>
            </div>

            {receipt.receipt_total_sen && (
              <div className="figure-block total-bill-figure">
                <span className="figure-label">TOTAL BILL</span>
                <span className="figure-value">{formatRm(receipt.receipt_total_sen)}</span>
              </div>
            )}
          </div>

          {isSplit && (
            <div className="split-explanation-box">
              <span className="split-icon" aria-hidden="true">💡</span>
              <p className="split-text">
                This bill was split. You are tracking your personal share of {formatRm(receipt.my_share_sen)} out of the total {formatRm(receipt.receipt_total_sen)}.
              </p>
            </div>
          )}

          <div className="detail-attributes-list">
            <div className="attribute-row">
              <span className="attr-label">Category:</span>
              <span className="attr-value">
                {receipt.category_name ? (
                  <span className="table-cat-badge">{receipt.category_name}</span>
                ) : (
                  "Uncategorized"
                )}
              </span>
            </div>

            {receipt.shared_with && (
              <div className="attribute-row">
                <span className="attr-label">Shared With:</span>
                <span className="attr-value">{receipt.shared_with}</span>
              </div>
            )}

            <div className="attribute-row">
              <span className="attr-label">Currency:</span>
              <span className="attr-value">{receipt.currency}</span>
            </div>
          </div>

          {receipt.notes && (
            <div className="detail-notes-section">
              <h3 className="notes-heading">Notes</h3>
              <p className="notes-body">{receipt.notes}</p>
            </div>
          )}
        </div>

        {/* Right Column: Attachment Document Preview */}
        <div className="card-surface detail-file-card">
          <div className="file-section-header">
            <h2 className="detail-section-title">Receipt Document</h2>
            {receipt.has_file && (
              <a
                href={fileUrl}
                download={receipt.original_filename}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary download-btn"
              >
                ⬇️ Download
              </a>
            )}
          </div>

          {receipt.has_file ? (
            <div className="file-display-area">
              {isPdf ? (
                <div className="pdf-display-box">
                  <span className="pdf-icon" aria-hidden="true">📄</span>
                  <p className="pdf-name">{receipt.original_filename}</p>
                  <a
                    href={fileUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-primary open-pdf-btn"
                  >
                    Open PDF in New Tab
                  </a>
                </div>
              ) : (
                <div className="image-display-box">
                  <img
                    src={fileUrl}
                    alt={`Receipt from ${receipt.merchant}`}
                    className="receipt-full-image"
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="no-file-box">
              <span className="no-file-icon" aria-hidden="true">📷</span>
              <p className="no-file-text">No receipt photo or PDF attached.</p>
              <Link to={`/receipts/${receipt.id}/edit`} className="btn-secondary add-file-link">
                Attach a file
              </Link>
            </div>
          )}
        </div>
      </div>

      <ConfirmModal
        isOpen={showDeleteModal}
        title="Move Receipt to Trash"
        message="Are you sure you want to move this receipt to the trash? It will be kept for 30 days before permanent deletion."
        confirmText="Move to Trash"
        isDanger={true}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setShowDeleteModal(false)}
      />
    </div>
  );
}
