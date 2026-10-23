// Purpose: Main application shell with React Router, auth guards, and responsive layout.
// Security: ProtectedRoute enforces authentication + must_change_password redirection;
//           AdminRoute independently checks role=admin before rendering admin pages.

import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';

// Layout components
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { BottomNav } from './components/BottomNav';

// Pages
import { LoginPage } from './pages/LoginPage';
import { ForcePasswordChangePage } from './pages/ForcePasswordChangePage';
import { DashboardPage } from './pages/DashboardPage';
import { ReceiptListPage } from './pages/ReceiptListPage';
import { ReceiptFormPage } from './pages/ReceiptFormPage';
import { ReceiptDetailPage } from './pages/ReceiptDetailPage';
import { MonthlyReportPage } from './pages/MonthlyReportPage';
import { TrashPage } from './pages/TrashPage';
import { CategoriesPage } from './pages/CategoriesPage';
import { SettingsPage } from './pages/SettingsPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { LoadingSpinner } from './components/LoadingSpinner';

/**
 * Wrapper for routes that require authentication.
 * Redirects unauthenticated users to /login.
 * Redirects users with must_change_password to /force-password-change.
 */
function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner message="Checking session…" />;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (user.must_change_password) {
    return <Navigate to="/force-password-change" replace />;
  }

  return <Outlet />;
}

/**
 * Additional guard for admin-only routes.
 * Returns 403-equivalent redirect if the user is not an admin.
 */
function AdminRoute() {
  const { user } = useAuth();

  if (!user || user.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

/**
 * Guard for the force-password-change page.
 * Only accessible when logged in AND must_change_password is true.
 */
function ForcePasswordRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner message="Checking session…" />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!user.must_change_password) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

/**
 * The main app shell layout rendered around all protected routes.
 * Contains the Navbar, Sidebar (with toggle), BottomNav, and a <main> content area.
 */
function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => setSidebarOpen(prev => !prev);
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="app-shell">
      <Navbar onToggleSidebar={toggleSidebar} />
      <div className="app-body">
        <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />
        <main className="app-main">
          <Outlet />
        </main>
      </div>
      <BottomNav />
    </div>
  );
}

/**
 * Top-level App component — sets up providers and routing.
 */
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Semi-public: authenticated but must change password */}
          <Route element={<ForcePasswordRoute />}>
            <Route path="/force-password-change" element={<ForcePasswordChangePage />} />
          </Route>

          {/* All authenticated routes wrapped in AppShell */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              {/* User routes */}
              <Route path="/" element={<DashboardPage />} />
              <Route path="/receipts" element={<ReceiptListPage />} />
              <Route path="/receipts/new" element={<ReceiptFormPage />} />
              <Route path="/receipts/:id" element={<ReceiptDetailPage />} />
              <Route path="/receipts/:id/edit" element={<ReceiptFormPage />} />
              <Route path="/reports" element={<MonthlyReportPage />} />
              <Route path="/trash" element={<TrashPage />} />
              <Route path="/categories" element={<CategoriesPage />} />
              <Route path="/settings" element={<SettingsPage />} />

              {/* Admin-only routes */}
              <Route element={<AdminRoute />}>
                <Route path="/admin" element={<AdminDashboardPage />} />
                <Route path="/admin/users" element={<AdminUsersPage />} />
              </Route>

              {/* Fallback — redirect unknown routes to dashboard */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
