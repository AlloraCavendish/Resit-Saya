// Purpose: Receipt creation and edition form page with file attachment and monetary conversion.
// Security: Client-side validation is convenience; relies on server bounds and deep file verification.

import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  createReceipt,
  getReceipt,
  updateReceipt,
  uploadReceiptFile,
  deleteReceiptFile,
  getReceiptFileUrl,
} from "../api/receipts";
import { getCategories } from "../api/categories";
import { getTodayString } from "../utils/date";
import { rmToSen, senToRmInput } from "../utils/money";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import "./ReceiptFormPage.css";

export function ReceiptFormPage() {
  const { id } = useParams();
  const isEditing = Boolean(id);
  const navigate = useNavigate();

  // Form Fields
  const [merchant, setMerchant] = useState("");
  const [receiptDate, setReceiptDate] = useState(getTodayString());
  const [myShareRm, setMyShareRm] = useState("");
  const [totalBillRm, setTotalBillRm] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [sharedWith, setSharedWith] = useState("");
  const [notes, setNotes] = useState("");

  // File upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreviewUrl, setFilePreviewUrl] = useState(null);
  const [existingFile, setExistingFile] = useState(null);

  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEditing);
  const [error, setError] = useState(null);

  // Load existing receipt if editing
  useEffect(() => {
    const initData = async () => {
      try {
        const catList = await getCategories();
        setCategories(catList);

        if (isEditing) {
          const receipt = await getReceipt(id);
          setMerchant(receipt.merchant);
          setReceiptDate(receipt.receipt_date);
          setMyShareRm(senToRmInput(receipt.my_share_sen));
          setTotalBillRm(receipt.receipt_total_sen ? senToRmInput(receipt.receipt_total_sen) : "");
          setCategoryId(receipt.category_id ? String(receipt.category_id) : "");
          setSharedWith(receipt.shared_with || "");
          setNotes(receipt.notes || "");
          if (receipt.has_file) {
            setExistingFile({
              filename: receipt.original_filename,
              url: getReceiptFileUrl(receipt.id),
            });
          }
        }
      } catch (err) {
        setError(err.message || "Failed to load receipt details.");
      } finally {
        setInitialLoading(false);
      }
    };
    initData();
  }, [id, isEditing]);

  // Handle local file selection and preview
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      if (file.type.startsWith("image/")) {
        const objectUrl = URL.createObjectURL(file);
        setFilePreviewUrl(objectUrl);
      } else {
        setFilePreviewUrl(null);
      }
    }
  };

  const handleRemoveExistingFile = async () => {
    if (!isEditing) return;
    try {
      setLoading(true);
      await deleteReceiptFile(id);
      setExistingFile(null);
    } catch (err) {
      setError(err.message || "Failed to remove attached file.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const shareSen = rmToSen(myShareRm);
    if (shareSen <= 0) {
      setError("Your share amount must be greater than RM 0.00.");
      return;
    }

    const totalSen = totalBillRm ? rmToSen(totalBillRm) : null;
    if (totalSen !== null && totalSen < shareSen) {
      setError("Total bill cannot be less than your own share.");
      return;
    }

    const payload = {
      merchant: merchant.trim(),
      receipt_date: receiptDate,
      my_share_sen: shareSen,
      receipt_total_sen: totalSen,
      category_id: categoryId ? Number(categoryId) : null,
      shared_with: sharedWith.trim() || null,
      notes: notes.trim() || null,
    };

    setLoading(true);
    try {
      let receiptId = id;
      if (isEditing) {
        await updateReceipt(id, payload);
      } else {
        const created = await createReceipt(payload);
        receiptId = created.id;
      }

      // Upload file if selected
      if (selectedFile) {
        await uploadReceiptFile(receiptId, selectedFile);
      }

      navigate(`/receipts/${receiptId}`);
    } catch (err) {
      setError(err.message || "Failed to save receipt. Please check your entries.");
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return <LoadingSpinner message="Loading receipt form..." />;
  }

  return (
    <div className="receipt-form-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">{isEditing ? "Edit Receipt" : "Add Receipt"}</h1>
          <p className="page-subtitle">
            {isEditing
              ? "Update your expense record and attachments"
              : "Record your share of a receipt or bill"}
          </p>
        </div>
        <Link to="/receipts" className="btn-secondary form-back-link">
          ← Back to Receipts
        </Link>
      </div>

      <ErrorMessage message={error} />

      <div className="card-surface form-card">
        <form onSubmit={handleSubmit} className="receipt-form">
          {/* Row 1: Merchant & Date */}
          <div className="form-row-2">
            <div className="form-group">
              <label htmlFor="receipt-merchant" className="form-label required">
                Merchant / Store Name
              </label>
              <input
                id="receipt-merchant"
                type="text"
                value={merchant}
                onChange={(e) => setMerchant(e.target.value)}
                placeholder="e.g. Kopitiam Ah Kow, Village Grocer"
                required
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="receipt-date" className="form-label required">
                Receipt Date
              </label>
              <input
                id="receipt-date"
                type="date"
                value={receiptDate}
                onChange={(e) => setReceiptDate(e.target.value)}
                required
                className="form-input"
              />
            </div>
          </div>

          {/* Row 2: Financial Shares (RM) */}
          <div className="form-row-2 financial-group">
            <div className="form-group">
              <label htmlFor="receipt-my-share" className="form-label required">
                My Share (RM)
              </label>
              <div className="currency-input-wrap">
                <span className="currency-prefix">RM</span>
                <input
                  id="receipt-my-share"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={myShareRm}
                  onChange={(e) => setMyShareRm(e.target.value)}
                  placeholder="0.00"
                  required
                  className="form-input currency-input"
                />
              </div>
              <span className="field-hint">
                The exact amount YOU paid or owe for this bill.
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="receipt-total" className="form-label">
                Total Bill (RM, Optional)
              </label>
              <div className="currency-input-wrap">
                <span className="currency-prefix">RM</span>
                <input
                  id="receipt-total"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={totalBillRm}
                  onChange={(e) => setTotalBillRm(e.target.value)}
                  placeholder="0.00"
                  className="form-input currency-input"
                />
              </div>
              <span className="field-hint">
                Fill if this receipt was split with friends or colleagues.
              </span>
            </div>
          </div>

          {/* Row 3: Category & Shared With */}
          <div className="form-row-2">
            <div className="form-group">
              <label htmlFor="receipt-category" className="form-label">
                Category
              </label>
              <select
                id="receipt-category"
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="form-input"
              >
                <option value="">-- Select Category (Optional) --</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="receipt-shared" className="form-label">
                Shared With (Optional)
              </label>
              <input
                id="receipt-shared"
                type="text"
                value={sharedWith}
                onChange={(e) => setSharedWith(e.target.value)}
                placeholder="e.g. Sarah, Amir, Team (3 pax)"
                className="form-input"
              />
            </div>
          </div>

          {/* Row 4: Notes */}
          <div className="form-group">
            <label htmlFor="receipt-notes" className="form-label">
              Notes (Optional)
            </label>
            <textarea
              id="receipt-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add details, meal descriptions, or reminders..."
              rows={3}
              className="form-input"
            />
          </div>

          {/* Row 5: File Attachment (Photo or PDF) */}
          <div className="form-group file-upload-section">
            <label htmlFor="receipt-file-input" className="form-label">
              Receipt Attachment (Optional - Photo or PDF)
            </label>

            {existingFile && (
              <div className="existing-file-box">
                <span className="existing-file-info">
                  📎 Current file: <strong>{existingFile.filename}</strong>
                </span>
                <button
                  type="button"
                  className="btn-danger-outline remove-file-btn"
                  onClick={handleRemoveExistingFile}
                  disabled={loading}
                >
                  Remove current file
                </button>
              </div>
            )}

            <div className="file-input-wrapper">
              <input
                id="receipt-file-input"
                type="file"
                accept="image/jpeg,image/png,image/webp,application/pdf"
                onChange={handleFileChange}
                disabled={loading}
                className="file-input-native"
              />
              <span className="file-input-hint">
                📸 On phones: capture with camera or select from gallery. Allowed formats: JPG, PNG, WebP, PDF (max 10MB).
              </span>
            </div>

            {/* Local image preview */}
            {filePreviewUrl && (
              <div className="preview-container">
                <p className="preview-label">New Photo Preview:</p>
                <img
                  src={filePreviewUrl}
                  alt="Receipt upload preview"
                  className="receipt-image-preview"
                />
              </div>
            )}
          </div>

          <div className="form-submit-actions">
            <Link to="/receipts" className="btn-secondary form-cancel-btn">
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary form-save-btn"
            >
              {loading ? "Saving receipt..." : isEditing ? "Update Receipt" : "Save Receipt"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
