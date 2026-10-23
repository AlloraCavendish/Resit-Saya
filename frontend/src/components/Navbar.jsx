// Purpose: Top navbar with live server clock, user identity, and session termination.
// Security: Renders authenticated username safely; executes secure server-side logout.

import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useServerClock } from "../hooks/useServerClock";
import "./Navbar.css";

export function Navbar({ onToggleSidebar }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { timeStr, dateStr } = useServerClock();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-left">
          {onToggleSidebar && (
            <button
              type="button"
              className="navbar-toggle-btn"
              onClick={onToggleSidebar}
              aria-label="Toggle navigation menu"
            >
              ☰
            </button>
          )}
          <Link to="/" className="navbar-brand">
            <span className="navbar-brand-icon" aria-hidden="true">🧾</span>
            <span className="navbar-brand-text">Resit Saya</span>
          </Link>
        </div>

        <div className="navbar-center">
          <div className="navbar-clock" title="Synchronized server time in Malaysia timezone">
            <span className="navbar-clock-time">{timeStr}</span>
            <span className="navbar-clock-date">{dateStr}</span>
          </div>
        </div>

        <div className="navbar-right">
          {user ? (
            <div className="navbar-user-area">
              <span className="navbar-username">
                {user.username}
                {user.role === "admin" && (
                  <span className="navbar-role-tag">Admin</span>
                )}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                className="btn-secondary navbar-logout-btn"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn-primary navbar-login-link">
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
