// Purpose: Trash management page for soft-deleted receipts with retention countdowns.
// Security: Enforces user isolation; requires explicit confirmation for permanent unrecoverable deletion.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTrash, restoreReceipt, permanentDeleteReceipt } from "../api/receipts";
import { formatRm } from "../utils/money";
import { formatDate } from "../utils/date";
import { ReceiptCard } from "../components/ReceiptCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import { ConfirmModal } from "../components/ConfirmModal";
import "./TrashPage.css";

export function TrashPage() {
  const [trashItems, setTrashItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [permDeleteId, setPermDeleteId] = useState(null);

  const fetchTrash = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTrash();
      setTrashItems(data.items || []);
    } catch (err) {
      setError(err.message || "Failed to load trash items.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrash();
  }, []);

  const handleRestore = async (id) => {
    try {
      await restoreReceipt(id);
      fetchTrash();
    } catch (err) {
      setError(err.message || "Failed to restore receipt.");
    }
  };

  const handlePermanentDelete = async () => {
    if (!permDeleteId) return;
    try {
      await permanentDeleteReceipt(permDeleteId);
      setPermDeleteId(null);
      fetchTrash();
    } catch (err) {
      setError(err.message || "Failed to delete receipt permanently.");
    }
  };

  return (
    <div className="trash-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Trash & Retention</h1>
          <p className="page-subtitle">
            Items in trash are automatically purged after 30 days
          </p>
        </div>
        <Link to="/receipts" className="btn-secondary">
          ← Back to Receipts
        </Link>
      </div>

      <ErrorMessage message={error} onRetry={fetchTrash} />

      <div className="trash-notice-card card-surface">
        <span className="notice-icon" aria-hidden="true">ℹ️</span>
        <div className="notice-body">
          <h2 className="notice-title">Automatic 30-Day Retention Policy</h2>
          <p className="notice-desc">
            Deleted receipts disappear from your reports and expense totals immediately. They are held here for 30 days so you can restore them if needed. After 30 days, receipts and attached files are permanently purged from disk.
          </p>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Checking trash bin..." />
      ) : trashItems.length === 0 ? (
        <div className="card-surface empty-trash-card">
          <span className="empty-icon" aria-hidden="true">🗑️</span>
          <p className="empty-text">Your trash bin is empty.</p>
        </div>
      ) : (
        <>
          {/* Mobile view: Cards (< 600px) */}
          <div className="trash-mobile-cards">
            {trashItems.map((r) => (
              <ReceiptCard
                key={r.id}
                receipt={r}
                isTrash={true}
                onRestore={handleRestore}
                onDelete={(id) => setPermDeleteId(id)}
              />
            ))}
          </div>

          {/* Desktop/Tablet Table view (>= 600px) */}
          <div className="card-surface trash-table-container">
            <table className="trash-table">
              <thead>
                <tr>
                  <th>Merchant</th>
                  <th>Receipt Date</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th>Time Remaining</th>
                  <th className="th-actions">Actions</th>
                </tr>
              </thead>
              <tbody>
                {trashItems.map((r) => (
                  <tr key={r.id}>
                    <td className="td-merchant">
                      <strong>{r.merchant}</strong>
                      {r.notes && <span className="td-sub-notes">{r.notes}</span>}
                    </td>
                    <td>{formatDate(r.receipt_date)}</td>
                    <td>{r.category_name || "-"}</td>
                    <td className="td-amount">{formatRm(r.my_share_sen)}</td>
                    <td>
                      <span className="retention-pill">
                        ⏳ {r.days_remaining} {r.days_remaining === 1 ? "day" : "days"} remaining
                      </span>
                    </td>
                    <td className="td-actions">
                      <div className="trash-actions-group">
                        <button
                          type="button"
                          className="btn-secondary btn-sm"
                          onClick={() => handleRestore(r.id)}
                        >
                          Restore
                        </button>
                        <button
                          type="button"
                          className="btn-danger-outline btn-sm"
                          onClick={() => setPermDeleteId(r.id)}
                        >
                          Delete permanently
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <ConfirmModal
        isOpen={Boolean(permDeleteId)}
        title="Permanently Delete Receipt?"
        message="This will delete the receipt record and any uploaded image or PDF from disk immediately. This action CANNOT be undone."
        confirmText="Delete permanently"
        isDanger={true}
        onConfirm={handlePermanentDelete}
        onCancel={() => setPermDeleteId(null)}
      />
    </div>
  );
}
