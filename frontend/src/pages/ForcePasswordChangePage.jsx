// Purpose: Forced password change screen for initial logins with temporary credentials.
// Security: Enforces minimum 10-character password policy; clears must_change_password flag upon completion.

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import * as authApi from "../api/auth";
import { ErrorMessage } from "../components/ErrorMessage";
import "./ForcePasswordChangePage.css";

export function ForcePasswordChangePage() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (newPassword.length < 10) {
      setError("New password must be at least 10 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      await refreshUser();
      navigate("/");
    } catch (err) {
      setError(err.message || "Failed to update password. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="force-pass-container">
      <div className="force-pass-card">
        <div className="force-pass-header">
          <span className="force-pass-icon" aria-hidden="true">🔑</span>
          <h1 className="force-pass-title">Set New Password</h1>
          <p className="force-pass-subtitle">
            Welcome, <strong>{user?.username}</strong>! For security purposes, please set your new personal password before accessing your account.
          </p>
        </div>

        <ErrorMessage message={error} />

        <form onSubmit={handleSubmit} className="force-pass-form">
          <div className="form-group">
            <label htmlFor="force-current" className="form-label">
              Temporary / Current Password
            </label>
            <input
              id="force-current"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter the password provided to you"
              required
              disabled={loading}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="force-new" className="form-label">
              New Password (minimum 10 characters)
            </label>
            <input
              id="force-new"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Choose a strong password"
              minLength={10}
              required
              disabled={loading}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="force-confirm" className="form-label">
              Confirm New Password
            </label>
            <input
              id="force-confirm"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your new password"
              minLength={10}
              required
              disabled={loading}
              className="form-input"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary force-pass-submit-btn"
          >
            {loading ? "Saving password..." : "Set Password & Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}
