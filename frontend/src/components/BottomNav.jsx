// Purpose: Mobile bottom tab navigation bar for phone viewports (< 600px).
// Security: Pure router navigation interface; adapts strictly to authenticated sessions.

import React from "react";
import { NavLink } from "react-router-dom";
import "./BottomNav.css";

export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Mobile Navigation">
      <NavLink
        to="/"
        end
        className={({ isActive }) => `bottom-nav-item ${isActive ? "active" : ""}`}
      >
        <span className="bottom-nav-icon" aria-hidden="true">📊</span>
        <span className="bottom-nav-label">Dashboard</span>
      </NavLink>

      <NavLink
        to="/receipts"
        end
        className={({ isActive }) => `bottom-nav-item ${isActive ? "active" : ""}`}
      >
        <span className="bottom-nav-icon" aria-hidden="true">🧾</span>
        <span className="bottom-nav-label">Receipts</span>
      </NavLink>

      <NavLink
        to="/receipts/new"
        className={({ isActive }) => `bottom-nav-item bottom-nav-add ${isActive ? "active" : ""}`}
        aria-label="Add receipt"
      >
        <span className="bottom-nav-icon-add" aria-hidden="true">➕</span>
        <span className="bottom-nav-label">Add</span>
      </NavLink>

      <NavLink
        to="/reports"
        className={({ isActive }) => `bottom-nav-item ${isActive ? "active" : ""}`}
      >
        <span className="bottom-nav-icon" aria-hidden="true">📈</span>
        <span className="bottom-nav-label">Reports</span>
      </NavLink>

      <NavLink
        to="/settings"
        className={({ isActive }) => `bottom-nav-item ${isActive ? "active" : ""}`}
      >
        <span className="bottom-nav-icon" aria-hidden="true">⚙️</span>
        <span className="bottom-nav-label">Settings</span>
      </NavLink>
    </nav>
  );
}
