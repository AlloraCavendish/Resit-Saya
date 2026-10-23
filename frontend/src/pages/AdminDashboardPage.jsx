// Purpose: Administrator aggregate dashboard page displaying system statistics and security audit trails.
// Security: Access strictly gated to users with admin role; exposes zero user receipts, financial sums, or file data.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminDashboard, getAuditLogs } from "../api/admin";
import { formatDate, formatDateTime } from "../utils/date";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import "./AdminDashboardPage.css";

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export function AdminDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Audit Log Filter
  const [eventFilter, setEventFilter] = useState("");
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const dashboardData = await getAdminDashboard();
      setData(dashboardData);
      setAuditLogs(dashboardData.recent_audit_logs || []);
    } catch (err) {
      setError(err.message || "Failed to load admin dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleFilterAuditLogs = async (e) => {
    e.preventDefault();
    setAuditLoading(true);
    try {
      const logs = await getAuditLogs(eventFilter || null);
      setAuditLogs(logs);
    } catch (err) {
      setError(err.message || "Failed to filter audit logs.");
    } finally {
      setAuditLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Compiling system metrics..." />;
  }

  // Find max daily count for rendering simple CSS bar heights
  const maxDayCount = Math.max(
    1,
    ...(data?.receipts_per_day_30d || []).map((d) => d.count)
  );

  return (
    <div className="admin-dashboard-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">🛡️ System Administration</h1>
          <p className="page-subtitle">
            Aggregate telemetry, user activity, and security audit logs (Version {data?.app_version})
          </p>
        </div>
        <Link to="/admin/users" className="btn-primary admin-users-btn">
          👥 Manage Users
        </Link>
      </div>

      <ErrorMessage message={error} onRetry={fetchDashboard} />

      {/* Metric Cards Grid */}
      <div className="admin-stats-grid">
        <div className="stat-card">
          <span className="stat-label">TOTAL USERS</span>
          <span className="stat-value">{data?.total_users}</span>
          <span className="stat-footer">
            {data?.active_users} active • {data?.disabled_users} disabled
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">ACTIVE RECEIPTS</span>
          <span className="stat-value">{data?.total_receipts}</span>
          <span className="stat-footer">
            {data?.trash_receipts} items pending retention purge
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">STORAGE CONSUMED</span>
          <span className="stat-value">{formatBytes(data?.total_storage_bytes)}</span>
          <span className="stat-footer">Across all user attachment folders</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">FAILED LOGINS (24H)</span>
          <span className={`stat-value ${data?.failed_logins_24h > 5 ? "stat-danger" : ""}`}>
            {data?.failed_logins_24h}
          </span>
          <span className="stat-footer">
            {data?.last_purge_job
              ? `Last retention purge: ${formatDateTime(data.last_purge_job.timestamp)} (${data.last_purge_job.count_purged} purged)`
              : "No retention purge executed yet"}
          </span>
        </div>
      </div>

      {/* 30-Day Activity Trend (CSS Bars, No Chart Library) */}
      <div className="card-surface trend-card">
        <div className="trend-header">
          <h2 className="section-title">Receipts Created (Last 30 Days)</h2>
          <span className="trend-subtitle">Daily creation activity</span>
        </div>

        <div className="trend-bars-container">
          {(data?.receipts_per_day_30d || []).map((day) => {
            const heightPercent = Math.round((day.count / maxDayCount) * 100);
            return (
              <div key={day.date} className="trend-bar-col" title={`${day.date}: ${day.count} receipts`}>
                <div className="trend-bar-track">
                  <div
                    className="trend-bar-fill"
                    style={{ "--bar-height": `${heightPercent}%` }}
                  />
                </div>
                <span className="trend-bar-count">{day.count > 0 ? day.count : ""}</span>
                <span className="trend-bar-date">{day.date.slice(8)}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Per-User Summary Table (No receipt content or money amounts) */}
      <div className="card-surface admin-section-card">
        <div className="admin-section-header">
          <h2 className="section-title">User Accounts Overview</h2>
          <Link to="/admin/users" className="section-action-link">
            User details & permissions →
          </Link>
        </div>

        <div className="table-responsive-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last Login</th>
                <th>Receipts Logged</th>
                <th>Uploads Size</th>
              </tr>
            </thead>
            <tbody>
              {(data?.users_summary || []).map((u) => (
                <tr key={u.id}>
                  <td>
                    <strong>{u.username}</strong>
                  </td>
                  <td>
                    <span className={`role-badge ${u.role === "admin" ? "admin" : "user"}`}>
                      {u.role}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${u.is_active ? "active" : "disabled"}`}>
                      {u.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td>{u.last_login_at ? formatDateTime(u.last_login_at) : "Never"}</td>
                  <td>{u.receipt_count}</td>
                  <td>{formatBytes(u.storage_bytes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Security Audit Log (Last 50, with event filter) */}
      <div className="card-surface admin-section-card">
        <div className="admin-section-header">
          <h2 className="section-title">Security & System Audit Log</h2>
          <form onSubmit={handleFilterAuditLogs} className="audit-filter-form">
            <select
              value={eventFilter}
              onChange={(e) => setEventFilter(e.target.value)}
              className="audit-filter-select"
            >
              <option value="">All Events</option>
              <option value="login_success">login_success</option>
              <option value="login_failed">login_failed</option>
              <option value="logout">logout</option>
              <option value="password_changed">password_changed</option>
              <option value="user_created">user_created</option>
              <option value="user_disabled">user_disabled</option>
              <option value="user_enabled">user_enabled</option>
              <option value="user_role_changed">user_role_changed</option>
              <option value="password_reset">password_reset</option>
              <option value="receipt_purged">receipt_purged</option>
              <option value="purge_job_run">purge_job_run</option>
            </select>
            <button
              type="submit"
              disabled={auditLoading}
              className="btn-secondary audit-filter-btn"
            >
              Filter
            </button>
          </form>
        </div>

        {auditLoading ? (
          <LoadingSpinner message="Filtering audit logs..." />
        ) : auditLogs.length === 0 ? (
          <p className="empty-audit-msg">No audit events match the selected criteria.</p>
        ) : (
          <div className="table-responsive-wrapper">
            <table className="admin-table audit-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event</th>
                  <th>Actor / Target</th>
                  <th>IP Address</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="td-audit-time">{formatDateTime(log.created_at)}</td>
                    <td>
                      <span className={`event-badge event-${log.event}`}>
                        {log.event}
                      </span>
                    </td>
                    <td>{log.username || (log.user_id ? `User #${log.user_id}` : "-")}</td>
                    <td className="td-mono">{log.ip || "-"}</td>
                    <td className="td-detail">{log.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
