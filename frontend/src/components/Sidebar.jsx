// Purpose: Sidebar navigation menu supporting responsive collapsible drawer and admin links.
// Security: Filters administrative route options in UI based on role; relies on backend 403 for actual access control.

import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import "./Sidebar.css";

export function Sidebar({ isOpen, onClose }) {
  const { user } = useAuth();
  const isAdmin = user && user.role === "admin";

  return (
    <>
      {isOpen && (
        <div
          className="sidebar-backdrop"
          onClick={onClose}
          role="presentation"
        />
      )}
      <aside className={`sidebar ${isOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-header">
          <span className="sidebar-header-title">Menu</span>
          {onClose && (
            <button
              type="button"
              className="sidebar-close-btn"
              onClick={onClose}
              aria-label="Close menu"
            >
              ✕
            </button>
          )}
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section">
            <span className="sidebar-section-title">EXPENSES</span>
            <NavLink
              to="/"
              end
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              onClick={onClose}
            >
              <span className="sidebar-icon">📊</span>
              <span>Dashboard</span>
            </NavLink>
            <NavLink
              to="/receipts"
              end
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              onClick={onClose}
            >
              <span className="sidebar-icon">🧾</span>
              <span>Receipts</span>
            </NavLink>
            <NavLink
              to="/receipts/new"
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              onClick={onClose}
            >
              <span className="sidebar-icon">➕</span>
              <span>Add Receipt</span>
            </NavLink>
            <NavLink
              to="/reports"
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              onClick={onClose}
            >
              <span className="sidebar-icon">📈</span>
              <span>Monthly Report</span>
            </NavLink>
          </div>

          <div className="sidebar-section">
            <span className="sidebar-section-title">MANAGEMENT</span>
            <NavLink
              to="/categories"
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              onClick={onClose}
            >
              <span className="sidebar-icon">🏷️</span>
              <span>Categories</span>
            </NavLink>
            <NavLink
              to="/trash"
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              onClick={onClose}
            >
              <span className="sidebar-icon">🗑️</span>
              <span>Trash</span>
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              onClick={onClose}
            >
              <span className="sidebar-icon">⚙️</span>
              <span>Settings</span>
            </NavLink>
          </div>

          {/* ADMIN-ONLY NAVIGATION SECTION */}
          {isAdmin && (
            <div className="sidebar-section admin-section">
              <span className="sidebar-section-title admin-title">ADMINISTRATION</span>
              <NavLink
                to="/admin"
                end
                className={({ isActive }) => `sidebar-link admin-link ${isActive ? "active" : ""}`}
                onClick={onClose}
              >
                <span className="sidebar-icon">🛡️</span>
                <span>Admin Dashboard</span>
              </NavLink>
              <NavLink
                to="/admin/users"
                className={({ isActive }) => `sidebar-link admin-link ${isActive ? "active" : ""}`}
                onClick={onClose}
              >
                <span className="sidebar-icon">👥</span>
                <span>User Management</span>
              </NavLink>
            </div>
          )}
        </nav>
      </aside>
    </>
  );
}
