// Purpose: Monthly expense report page with month navigation and category breakdowns.
// Security: Exclusively scopes financial aggregations to the authenticated user.

import React, { useEffect, useState } from "react";
import { getMonthlyReport } from "../api/reports";
import { formatRm } from "../utils/money";
import { getCurrentMonthString } from "../utils/date";
import { CategoryBar } from "../components/CategoryBar";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import "./MonthlyReportPage.css";

export function MonthlyReportPage() {
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonthString());
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchReport = async (month) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMonthlyReport(month);
      setReport(data);
    } catch (err) {
      setError(err.message || "Failed to load monthly report.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport(selectedMonth);
  }, [selectedMonth]);

  const handlePrevMonth = () => {
    const [y, m] = selectedMonth.split("-").map(Number);
    let newY = y;
    let newM = m - 1;
    if (newM < 1) {
      newM = 12;
      newY -= 1;
    }
    setSelectedMonth(`${newY}-${String(newM).padStart(2, "0")}`);
  };

  const handleNextMonth = () => {
    const [y, m] = selectedMonth.split("-").map(Number);
    let newY = y;
    let newM = m + 1;
    if (newM > 12) {
      newM = 1;
      newY += 1;
    }
    setSelectedMonth(`${newY}-${String(newM).padStart(2, "0")}`);
  };

  // Format month for header (e.g. "October 2026")
  const formatMonthTitle = (monthStr) => {
    try {
      const [y, m] = monthStr.split("-").map(Number);
      const d = new Date(y, m - 1, 1);
      return d.toLocaleDateString("en-MY", { month: "long", year: "numeric" });
    } catch {
      return monthStr;
    }
  };

  return (
    <div className="report-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Monthly Expense Report</h1>
          <p className="page-subtitle">Track your spending trends and category distribution</p>
        </div>

        {/* Month Picker Controls with Prev / Next */}
        <div className="month-picker-container">
          <button
            type="button"
            className="btn-secondary month-nav-btn"
            onClick={handlePrevMonth}
            aria-label="Previous Month"
          >
            ◀
          </button>
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => e.target.value && setSelectedMonth(e.target.value)}
            className="month-picker-input"
          />
          <button
            type="button"
            className="btn-secondary month-nav-btn"
            onClick={handleNextMonth}
            aria-label="Next Month"
          >
            ▶
          </button>
        </div>
      </div>

      <ErrorMessage message={error} onRetry={() => fetchReport(selectedMonth)} />

      {loading ? (
        <LoadingSpinner message="Calculating monthly expenses..." />
      ) : report ? (
        <div className="report-content">
          {/* Summary Overview Cards */}
          <div className="report-summary-grid">
            <div className="card-surface summary-card total-card">
              <span className="summary-card-label">TOTAL SPENT IN {formatMonthTitle(report.month).toUpperCase()}</span>
              <span className="summary-card-value primary">{formatRm(report.total_sen)}</span>
              <span className="summary-card-sub">{report.receipt_count} receipts recorded</span>
            </div>

            <div className="card-surface summary-card">
              <span className="summary-card-label">PREVIOUS MONTH ({formatMonthTitle(report.previous_month)})</span>
              <span className="summary-card-value">{formatRm(report.previous_month_total_sen)}</span>
              <div className="summary-card-diff">
                {report.diff_percentage !== null ? (
                  <span className={report.diff_sen >= 0 ? "diff-pill up" : "diff-pill down"}>
                    {report.diff_sen >= 0 ? "+" : ""}{formatRm(report.diff_sen)} ({report.diff_percentage}%)
                  </span>
                ) : (
                  <span className="summary-card-sub">No prior comparison</span>
                )}
              </div>
            </div>
          </div>

          {/* Breakdown Section */}
          <div className="card-surface report-breakdown-card">
            <h2 className="breakdown-title">Spending by Category</h2>

            {report.categories.length === 0 ? (
              <div className="empty-report-state">
                <p>No receipts found for {formatMonthTitle(report.month)}.</p>
              </div>
            ) : (
              <div className="breakdown-layout">
                {/* Visual Category Bars */}
                <div className="breakdown-bars-col">
                  {report.categories.map((c, idx) => (
                    <CategoryBar
                      key={c.category_id || idx}
                      name={c.category_name}
                      amountFormatted={formatRm(c.total_sen)}
                      percentage={c.percentage}
                      count={c.count}
                    />
                  ))}
                </div>

                {/* Breakdown Data Table */}
                <div className="breakdown-table-col">
                  <table className="breakdown-table">
                    <thead>
                      <tr>
                        <th>Category</th>
                        <th>Receipts</th>
                        <th>Amount</th>
                        <th>Share</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.categories.map((c, idx) => (
                        <tr key={c.category_id || idx}>
                          <td className="td-cat-name">{c.category_name}</td>
                          <td className="td-cat-count">{c.count}</td>
                          <td className="td-cat-amount">{formatRm(c.total_sen)}</td>
                          <td className="td-cat-pct">{c.percentage.toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr>
                        <th>Total</th>
                        <th>{report.receipt_count}</th>
                        <th>{formatRm(report.total_sen)}</th>
                        <th>100.0%</th>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
