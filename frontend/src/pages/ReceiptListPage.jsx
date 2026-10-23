// Purpose: Receipts listing page with multi-field search, date and category filters, and pagination.
// Security: Filters strictly by user session on backend; provides responsive mobile-cards / desktop-tables.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getReceipts, deleteReceipt } from "../api/receipts";
import { getCategories } from "../api/categories";
import { formatRm } from "../utils/money";
import { formatDate } from "../utils/date";
import { ReceiptCard } from "../components/ReceiptCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import { ConfirmModal } from "../components/ConfirmModal";
import "./ReceiptListPage.css";

export function ReceiptListPage() {
  const [receipts, setReceipts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(15);

  // Filters state
  const [searchTerm, setSearchTerm] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Soft-delete modal state
  const [deleteId, setDeleteId] = useState(null);

  const fetchCategories = async () => {
    try {
      const data = await getCategories();
      setCategories(data);
    } catch {
      // Ignore category load error
    }
  };

  const fetchReceipts = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getReceipts({
        search: searchTerm,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        categoryId: selectedCategory ? Number(selectedCategory) : undefined,
        page,
        pageSize,
      });
      setReceipts(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      setError(err.message || "Failed to load receipts.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchReceipts();
  }, [page, startDate, endDate, selectedCategory]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchReceipts();
  };

  const handleClearFilters = () => {
    setSearchTerm("");
    setStartDate("");
    setEndDate("");
    setSelectedCategory("");
    setPage(1);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteId) return;
    try {
      await deleteReceipt(deleteId);
      setDeleteId(null);
      fetchReceipts();
    } catch (err) {
      setError(err.message || "Failed to delete receipt.");
    }
  };

  return (
    <div className="receipt-list-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">My Receipts</h1>
          <p className="page-subtitle">
            Showing {receipts.length} of {total} receipts
          </p>
        </div>
        <Link to="/receipts/new" className="btn-primary list-add-btn">
          ➕ Add Receipt
        </Link>
      </div>

      <ErrorMessage message={error} onRetry={fetchReceipts} />

      {/* Filter and Search Bar */}
      <div className="card-surface filter-card">
        <form onSubmit={handleSearchSubmit} className="search-form">
          <div className="search-input-wrap">
            <span className="search-icon" aria-hidden="true">🔍</span>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search merchant, notes, shared with..."
              className="search-input"
            />
          </div>
          <button type="submit" className="btn-primary search-btn">
            Search
          </button>
        </form>

        <div className="filter-controls-grid">
          <div className="filter-item">
            <label htmlFor="filter-cat" className="filter-label">
              Category
            </label>
            <select
              id="filter-cat"
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="filter-select"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-item">
            <label htmlFor="filter-start" className="filter-label">
              From Date
            </label>
            <input
              id="filter-start"
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setPage(1);
              }}
              className="filter-date"
            />
          </div>

          <div className="filter-item">
            <label htmlFor="filter-end" className="filter-label">
              To Date
            </label>
            <input
              id="filter-end"
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setPage(1);
              }}
              className="filter-date"
            />
          </div>

          <div className="filter-actions-item">
            <button
              type="button"
              className="btn-secondary filter-clear-btn"
              onClick={handleClearFilters}
            >
              Clear filters
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading receipts..." />
      ) : receipts.length === 0 ? (
        <div className="card-surface empty-receipts-card">
          <span className="empty-icon">🧾</span>
          <p className="empty-text">No receipts matched your criteria.</p>
          <div className="empty-btn-wrap">
            <button
              type="button"
              onClick={handleClearFilters}
              className="btn-secondary"
            >
              Reset filters
            </button>
            <Link to="/receipts/new" className="btn-primary">
              Add new receipt
            </Link>
          </div>
        </div>
      ) : (
        <>
          {/* Mobile view: Cards (Phone < 600px) */}
          <div className="receipts-mobile-cards">
            {receipts.map((r) => (
              <ReceiptCard
                key={r.id}
                receipt={r}
                onDelete={(id) => setDeleteId(id)}
              />
            ))}
          </div>

          {/* Desktop & Tablet view: Clean Data Table (>= 600px) */}
          <div className="card-surface receipts-table-container">
            <table className="receipts-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Merchant</th>
                  <th>Category</th>
                  <th>My Share</th>
                  <th>Total Bill</th>
                  <th>File</th>
                  <th className="th-actions">Actions</th>
                </tr>
              </thead>
              <tbody>
                {receipts.map((r) => (
                  <tr key={r.id}>
                    <td className="td-date">{formatDate(r.receipt_date)}</td>
                    <td className="td-merchant">
                      <Link to={`/receipts/${r.id}`} className="table-merchant-link">
                        {r.merchant}
                      </Link>
                      {r.shared_with && (
                        <span className="table-shared-hint">
                          Shared: {r.shared_with}
                        </span>
                      )}
                    </td>
                    <td className="td-category">
                      {r.category_name ? (
                        <span className="table-cat-badge">{r.category_name}</span>
                      ) : (
                        <span className="table-cat-none">-</span>
                      )}
                    </td>
                    <td className="td-share">{formatRm(r.my_share_sen)}</td>
                    <td className="td-total">
                      {r.receipt_total_sen ? formatRm(r.receipt_total_sen) : "-"}
                    </td>
                    <td className="td-file">
                      {r.has_file ? (
                        <span className="table-file-pill" title="File attached">
                          📎 Yes
                        </span>
                      ) : (
                        <span className="table-no-file">-</span>
                      )}
                    </td>
                    <td className="td-actions">
                      <div className="table-action-btns">
                        <Link to={`/receipts/${r.id}`} className="table-btn-view">
                          View
                        </Link>
                        <Link to={`/receipts/${r.id}/edit`} className="table-btn-edit">
                          Edit
                        </Link>
                        <button
                          type="button"
                          className="table-btn-del"
                          onClick={() => setDeleteId(r.id)}
                          aria-label={`Move receipt ${r.merchant} to trash`}
                        >
                          Trash
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="pagination-bar">
              <button
                type="button"
                className="btn-secondary pagination-btn"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                className="btn-secondary pagination-btn"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {/* Soft-delete confirmation modal */}
      <ConfirmModal
        isOpen={Boolean(deleteId)}
        title="Move to Trash"
        message="Are you sure you want to move this receipt to the trash? It will be held for 30 days before permanent deletion."
        confirmText="Move to Trash"
        isDanger={true}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
