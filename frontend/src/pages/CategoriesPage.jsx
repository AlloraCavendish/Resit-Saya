// Purpose: Category management page allowing users to add, rename, and delete custom categories.
// Security: Scoped to user's own categories; prevents tampering with other users' categories.

import React, { useEffect, useState } from "react";
import { getCategories, createCategory, updateCategory, deleteCategory } from "../api/categories";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import { ConfirmModal } from "../components/ConfirmModal";
import "./CategoriesPage.css";

export function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // New Category State
  const [newCatName, setNewCatName] = useState("");
  const [adding, setAdding] = useState(false);

  // Rename State
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");

  // Delete Modal State
  const [deleteCatId, setDeleteCatId] = useState(null);

  const fetchCategories = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCategories();
      setCategories(data);
    } catch (err) {
      setError(err.message || "Failed to load categories.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!newCatName.trim()) return;

    setAdding(true);
    setError(null);
    try {
      await createCategory(newCatName.trim());
      setNewCatName("");
      fetchCategories();
    } catch (err) {
      setError(err.message || "Failed to create category.");
    } finally {
      setAdding(false);
    }
  };

  const handleStartEdit = (cat) => {
    setEditingId(cat.id);
    setEditName(cat.name);
  };

  const handleSaveEdit = async (catId) => {
    if (!editName.trim()) return;
    try {
      await updateCategory(catId, editName.trim());
      setEditingId(null);
      fetchCategories();
    } catch (err) {
      setError(err.message || "Failed to rename category.");
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteCatId) return;
    try {
      await deleteCategory(deleteCatId);
      setDeleteCatId(null);
      fetchCategories();
    } catch (err) {
      setError(err.message || "Failed to delete category.");
    }
  };

  return (
    <div className="categories-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Expense Categories</h1>
          <p className="page-subtitle">
            Manage your personal expense categories and tags
          </p>
        </div>
      </div>

      <ErrorMessage message={error} onRetry={fetchCategories} />

      {/* Add New Category Form */}
      <div className="card-surface add-cat-card">
        <h2 className="add-cat-title">Create New Category</h2>
        <form onSubmit={handleAddSubmit} className="add-cat-form">
          <input
            type="text"
            value={newCatName}
            onChange={(e) => setNewCatName(e.target.value)}
            placeholder="e.g. Subscriptions, Pet Care, Gifts"
            maxLength={64}
            required
            disabled={adding}
            className="form-input add-cat-input"
          />
          <button
            type="submit"
            disabled={adding || !newCatName.trim()}
            className="btn-primary add-cat-btn"
          >
            {adding ? "Adding..." : "Add Category"}
          </button>
        </form>
      </div>

      {/* Categories List */}
      <div className="card-surface categories-list-card">
        <h2 className="categories-list-title">
          Your Categories ({categories.length})
        </h2>

        {loading ? (
          <LoadingSpinner message="Loading categories..." />
        ) : categories.length === 0 ? (
          <p className="empty-cat-text">No categories found.</p>
        ) : (
          <ul className="categories-list">
            {categories.map((cat) => (
              <li key={cat.id} className="category-item">
                {editingId === cat.id ? (
                  <div className="category-edit-form">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      maxLength={64}
                      className="form-input edit-cat-input"
                    />
                    <div className="edit-btn-group">
                      <button
                        type="button"
                        className="btn-primary btn-xs"
                        onClick={() => handleSaveEdit(cat.id)}
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        className="btn-secondary btn-xs"
                        onClick={() => setEditingId(null)}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="category-details">
                      <span className="category-name-badge">🏷️ {cat.name}</span>
                      <span className="category-count">
                        {cat.receipt_count}{" "}
                        {cat.receipt_count === 1 ? "receipt" : "receipts"}
                      </span>
                    </div>
                    <div className="category-actions">
                      <button
                        type="button"
                        className="btn-secondary btn-xs"
                        onClick={() => handleStartEdit(cat)}
                      >
                        Rename
                      </button>
                      <button
                        type="button"
                        className="btn-danger-outline btn-xs"
                        onClick={() => setDeleteCatId(cat.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <ConfirmModal
        isOpen={Boolean(deleteCatId)}
        title="Delete Category?"
        message="Deleting this category will set associated receipts to Uncategorized. Receipts will not be deleted."
        confirmText="Delete Category"
        isDanger={true}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteCatId(null)}
      />
    </div>
  );
}
