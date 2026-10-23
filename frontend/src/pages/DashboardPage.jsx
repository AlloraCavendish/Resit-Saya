// Purpose: Main user dashboard displaying expense totals, category bars, and recent receipts.
// Security: Scoped to authenticated user data; sanitizes display numbers and text strings.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMonthlyReport } from "../api/reports";
import { getReceipts } from "../api/receipts";
import { useServerClock } from "../hooks/useServerClock";
import { formatRm } from "../utils/money";
import { getCurrentMonthString } from "../utils/date";
import { CategoryBar } from "../components/CategoryBar";
import { ReceiptCard } from "../components/ReceiptCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import "./DashboardPage.css";

export function DashboardPage() {
  const [report, setReport] = useState(null);
  const [recentReceipts, setRecentReceipts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const clock = useServerClock();
  const currentMonth = getCurrentMonthString();

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [reportData, receiptsData] = await Promise.all([
        getMonthlyReport(currentMonth),
        getReceipts({ pageSize: 5 }),
      ]);
      setReport(reportData);
      setRecentReceipts(receiptsData.items || []);
    } catch (err) {
      setError(err.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [currentMonth]);

  if (loading) {
    return <LoadingSpinner message="Loading your expense overview..." />;
  }

  const topCategories = (report?.categories || []).slice(0, 5);

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Expense Dashboard</h1>
          <p className="page-subtitle">Overview of your personal spending this month</p>
        </div>
        <Link to="/receipts/new" className="btn-primary dashboard-add-btn">
          ➕ Add Receipt
        </Link>
      </div>

      <ErrorMessage message={error} onRetry={loadDashboardData} />

      {/* Hero Stat Cards */}
      <div className="dashboard-stats-grid">
        <div className="stat-card stat-total">
          <div className="stat-header">
            <span className="stat-label">THIS MONTH'S TOTAL</span>
            <span className="stat-icon">💰</span>
          </div>
          <div className="stat-value">{formatRm(report?.total_sen || 0)}</div>
          <div className="stat-footer">
            {report?.diff_percentage !== null && report?.diff_percentage !== undefined ? (
              <span className={report.diff_percentage >= 0 ? "stat-diff-up" : "stat-diff-down"}>
                {report.diff_percentage >= 0 ? "▲" : "▼"} {Math.abs(report.diff_percentage)}% vs last month ({formatRm(report.previous_month_total_sen)})
              </span>
            ) : (
              <span className="stat-diff-neutral">
                Previous month: {formatRm(report?.previous_month_total_sen || 0)}
              </span>
            )}
          </div>
        </div>

        <div className="stat-card stat-count">
          <div className="stat-header">
            <span className="stat-label">RECEIPTS LOGGED</span>
            <span className="stat-icon">🧾</span>
          </div>
          <div className="stat-value">{report?.receipt_count || 0}</div>
          <div className="stat-footer">
            <span className="stat-count-sub">In {report?.month || currentMonth}</span>
          </div>
        </div>

        <div className="stat-card stat-clock">
          <div className="stat-header">
            <span className="stat-label">LOCAL SERVER TIME</span>
            <span className="stat-icon">🕒</span>
          </div>
          <div className="stat-time-val">{clock.timeStr}</div>
          <div className="stat-footer">
            <span className="stat-clock-details">
              {clock.dateStr} • {clock.timezone}
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid: Categories & Recent Receipts */}
      <div className="dashboard-main-grid">
        {/* Top Categories Breakdown */}
        <div className="card-surface dashboard-section">
          <div className="section-header">
            <h2 className="section-title">Top Categories</h2>
            <Link to="/reports" className="section-action-link">
              Full breakdown →
            </Link>
          </div>

          {topCategories.length === 0 ? (
            <div className="empty-state">
              <p>No expenses recorded this month yet.</p>
              <Link to="/receipts/new" className="empty-action-link">
                Record your first receipt
              </Link>
            </div>
          ) : (
            <div className="category-bars-list">
              {topCategories.map((cat, idx) => (
                <CategoryBar
                  key={cat.category_id || idx}
                  name={cat.category_name}
                  amountFormatted={formatRm(cat.total_sen)}
                  percentage={cat.percentage}
                  count={cat.count}
                />
              ))}
            </div>
          )}
        </div>

        {/* 5 Most Recent Receipts */}
        <div className="card-surface dashboard-section">
          <div className="section-header">
            <h2 className="section-title">Recent Receipts</h2>
            <Link to="/receipts" className="section-action-link">
              View all →
            </Link>
          </div>

          {recentReceipts.length === 0 ? (
            <div className="empty-state">
              <p>No recent receipts found.</p>
              <Link to="/receipts/new" className="empty-action-link">
                Add a new receipt
              </Link>
            </div>
          ) : (
            <div className="recent-receipts-list">
              {recentReceipts.map((receipt) => (
                <ReceiptCard key={receipt.id} receipt={receipt} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
