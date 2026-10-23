// Purpose: Admin user management page — list, create, enable/disable, change role, reset password.
// Security: Only rendered behind admin-role route guard; all mutation endpoints independently
//           enforce admin role server-side (403 for non-admins). ConfirmModal gates destructive ops.

import React, { useState, useEffect, useCallback } from 'react';
import { listAdminUsers, createAdminUser, updateAdminUser, resetUserPassword } from '../api/admin';
import { ConfirmModal } from '../components/ConfirmModal';
import { ErrorMessage } from '../components/ErrorMessage';
import { LoadingSpinner } from '../components/LoadingSpinner';
import './AdminUsersPage.css';

export function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Create user form state
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ username: '', email: '', password: '', role: 'user' });
  const [createError, setCreateError] = useState(null);
  const [creating, setCreating] = useState(false);

  // Reset password modal
  const [resetTarget, setResetTarget] = useState(null); // { id, username }
  const [resetPassword, setResetPasswordVal] = useState('');
  const [resetError, setResetError] = useState(null);
  const [resetting, setResetting] = useState(false);

  // Confirm modal for disable/enable/role change
  const [confirm, setConfirm] = useState(null); // { title, message, onConfirm }

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listAdminUsers();
      setUsers(data);
    } catch (err) {
      setError(err.message || 'Failed to load users.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // --- Create user ---
  function handleCreateChange(e) {
    const { name, value } = e.target;
    setCreateForm(f => ({ ...f, [name]: value }));
  }

  async function handleCreateSubmit(e) {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      await createAdminUser(createForm);
      setCreateForm({ username: '', email: '', password: '', role: 'user' });
      setShowCreate(false);
      await loadUsers();
    } catch (err) {
      setCreateError(err.message || 'Failed to create user.');
    } finally {
      setCreating(false);
    }
  }

  // --- Enable / Disable ---
  function promptToggleActive(user) {
    const action = user.is_active ? 'disable' : 'enable';
    setConfirm({
      title: `${action.charAt(0).toUpperCase() + action.slice(1)} user`,
      message: `Are you sure you want to ${action} "${user.username}"?`,
      onConfirm: async () => {
        try {
          await updateAdminUser(user.id, { is_active: !user.is_active });
          await loadUsers();
        } catch (err) {
          setError(err.message || `Failed to ${action} user.`);
        }
        setConfirm(null);
      },
    });
  }

  // --- Change role ---
  function promptChangeRole(user) {
    const newRole = user.role === 'admin' ? 'user' : 'admin';
    setConfirm({
      title: 'Change role',
      message: `Change "${user.username}" role from "${user.role}" to "${newRole}"?`,
      onConfirm: async () => {
        try {
          await updateAdminUser(user.id, { role: newRole });
          await loadUsers();
        } catch (err) {
          setError(err.message || 'Failed to change role.');
        }
        setConfirm(null);
      },
    });
  }

  // --- Reset password ---
  function openResetModal(user) {
    setResetTarget(user);
    setResetPasswordVal('');
    setResetError(null);
  }

  async function handleResetSubmit(e) {
    e.preventDefault();
    setResetting(true);
    setResetError(null);
    try {
      await resetUserPassword(resetTarget.id, resetPassword);
      setResetTarget(null);
    } catch (err) {
      setResetError(err.message || 'Failed to reset password.');
    } finally {
      setResetting(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="admin-users-page">
      <div className="admin-users-header">
        <h1>User Management</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(s => !s)}>
          {showCreate ? 'Cancel' : '+ New User'}
        </button>
      </div>

      {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

      {/* Create user form */}
      {showCreate && (
        <section className="admin-users-create-panel">
          <h2>Create New User</h2>
          {createError && <ErrorMessage message={createError} onDismiss={() => setCreateError(null)} />}
          <form className="admin-users-create-form" onSubmit={handleCreateSubmit}>
            <div className="form-group">
              <label htmlFor="cu-username">Username</label>
              <input
                id="cu-username"
                name="username"
                type="text"
                required
                autoComplete="off"
                value={createForm.username}
                onChange={handleCreateChange}
              />
            </div>
            <div className="form-group">
              <label htmlFor="cu-email">Email</label>
              <input
                id="cu-email"
                name="email"
                type="email"
                required
                autoComplete="off"
                value={createForm.email}
                onChange={handleCreateChange}
              />
            </div>
            <div className="form-group">
              <label htmlFor="cu-password">Temporary Password</label>
              <input
                id="cu-password"
                name="password"
                type="password"
                required
                minLength={10}
                autoComplete="new-password"
                value={createForm.password}
                onChange={handleCreateChange}
              />
              <span className="form-hint">Min 10 characters. User must change on first login.</span>
            </div>
            <div className="form-group">
              <label htmlFor="cu-role">Role</label>
              <select id="cu-role" name="role" value={createForm.role} onChange={handleCreateChange}>
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={creating}>
                {creating ? 'Creating…' : 'Create User'}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>
                Cancel
              </button>
            </div>
          </form>
        </section>
      )}

      {/* Users table */}
      <section className="admin-users-table-section">
        <div className="table-scroll">
          <table className="admin-users-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last Login</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id} className={user.is_active ? '' : 'row-disabled'}>
                  <td data-label="Username">
                    <span className="username-cell">{user.username}</span>
                    {user.must_change_password && (
                      <span className="badge badge-warn" title="Must change password">PW!</span>
                    )}
                  </td>
                  <td data-label="Email">{user.email}</td>
                  <td data-label="Role">
                    <span className={`badge ${user.role === 'admin' ? 'badge-admin' : 'badge-user'}`}>
                      {user.role}
                    </span>
                  </td>
                  <td data-label="Status">
                    <span className={`badge ${user.is_active ? 'badge-ok' : 'badge-off'}`}>
                      {user.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td data-label="Last Login">
                    {user.last_login_at
                      ? new Date(user.last_login_at).toLocaleString('en-MY')
                      : '—'}
                  </td>
                  <td data-label="Actions" className="actions-cell">
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => promptToggleActive(user)}
                    >
                      {user.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => promptChangeRole(user)}
                    >
                      Make {user.role === 'admin' ? 'User' : 'Admin'}
                    </button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => openResetModal(user)}
                    >
                      Reset PW
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={6} className="empty-row">No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Confirm modal */}
      <ConfirmModal
        isOpen={!!confirm}
        title={confirm?.title || ''}
        message={confirm?.message || ''}
        onConfirm={confirm?.onConfirm || (() => {})}
        onCancel={() => setConfirm(null)}
      />

      {/* Reset password modal */}
      {resetTarget && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="reset-title">
          <div className="modal-box">
            <h2 id="reset-title">Reset Password — {resetTarget.username}</h2>
            {resetError && <ErrorMessage message={resetError} onDismiss={() => setResetError(null)} />}
            <form onSubmit={handleResetSubmit}>
              <div className="form-group">
                <label htmlFor="rp-password">New Temporary Password</label>
                <input
                  id="rp-password"
                  type="password"
                  required
                  minLength={10}
                  autoComplete="new-password"
                  value={resetPassword}
                  onChange={e => setResetPasswordVal(e.target.value)}
                />
                <span className="form-hint">Min 10 characters. User must change on next login.</span>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-danger" disabled={resetting}>
                  {resetting ? 'Resetting…' : 'Reset Password'}
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setResetTarget(null)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


