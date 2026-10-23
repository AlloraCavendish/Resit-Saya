// Purpose: User settings page for credential updates and account preferences.
// Security: Requires current password; invalidates other active user sessions on password change.

import React, { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import * as authApi from "../api/auth";
import { formatDate } from "../utils/date";
import { ErrorMessage } from "../components/ErrorMessage";
import "./SettingsPage.css";

export function SettingsPage() {
  const { user } = useAuth();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

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
      setSuccess("Your password was updated successfully. Other active sessions have been signed out.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.message || "Failed to change password. Please check your current password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Account Settings</h1>
          <p className="page-subtitle">Manage your credentials and security</p>
        </div>
      </div>

      <ErrorMessage message={error} />

      {success && (
        <div className="settings-success-banner" role="status">
          ✅ {success}
        </div>
      )}

      {/* Account Profile Card */}
      <div className="card-surface settings-card">
        <h2 className="settings-section-title">Profile Information</h2>
        <div className="profile-details-grid">
          <div className="profile-field">
            <span className="profile-label">Username</span>
            <span className="profile-value">{user?.username}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Email</span>
            <span className="profile-value">{user?.email}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Role</span>
            <span className="profile-value capitalize">{user?.role}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Member Since</span>
            <span className="profile-value">{formatDate(user?.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Change Password Card */}
      <div className="card-surface settings-card">
        <h2 className="settings-section-title">Change Password</h2>
        <p className="settings-section-desc">
          Ensure your account is using a long, secure password. Changing your password will invalidate all other active sessions across devices.
        </p>

        <form onSubmit={handlePasswordSubmit} className="change-pass-form">
          <div className="form-group">
            <label htmlFor="settings-current-pass" className="form-label required">
              Current Password
            </label>
            <input
              id="settings-current-pass"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter your current password"
              required
              disabled={loading}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="settings-new-pass" className="form-label required">
              New Password (minimum 10 characters)
            </label>
            <input
              id="settings-new-pass"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new strong password"
              minLength={10}
              required
              disabled={loading}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="settings-confirm-pass" className="form-label required">
              Confirm New Password
            </label>
            <input
              id="settings-confirm-pass"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter new password"
              minLength={10}
              required
              disabled={loading}
              className="form-input"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary update-pass-btn"
          >
            {loading ? "Updating password..." : "Update Password"}
          </button>
        </form>
      </div>
    </div>
  );
}
