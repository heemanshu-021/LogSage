import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { apiFetch } from '../lib/api'

export default function Navbar({ health, openIncidentsCount, username, onLogout, onPasswordChanged }) {
  const location = useLocation()
  const [showPasswordForm, setShowPasswordForm] = useState(false)
  const [passwordError, setPasswordError] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)

  const navLinks = [
    { path: '/', label: 'Overview', icon: '⚡' },
    { path: '/scan', label: 'Ingest & Scan', icon: '📥' },
    { path: '/incidents', label: 'Incidents', icon: '🚨', badge: openIncidentsCount > 0 ? openIncidentsCount : null },
    { path: '/triage', label: 'Triage Room', icon: '🛠️' },
    { path: '/runbooks', label: 'Runbooks', icon: '📖' },
  ]

  const isModelReady = health?.ml_model_loaded
  const isApiOnline = health?.status === 'ok'

  async function handlePasswordSubmit(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const currentPassword = form.get('currentPassword')
    const newPassword = form.get('newPassword')
    const confirmPassword = form.get('confirmPassword')
    if (newPassword !== confirmPassword) {
      setPasswordError('The new passwords do not match.')
      return
    }
    setPasswordError('')
    setPasswordSaving(true)
    try {
      const response = await apiFetch('/api/auth/password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      })
      const body = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(body.detail || `Password change failed (HTTP ${response.status})`)
      onPasswordChanged?.()
    } catch (error) {
      setPasswordError(error.message || 'Password change failed.')
    } finally {
      setPasswordSaving(false)
    }
  }

  return (
    <header className="navbar">
      <div className="navbar-left">
        <Link to="/" className="brand">
          <div className="brand-logo-glow">🛡️</div>
          <div className="brand-text">
            <span className="brand-title">LogSage</span>
            <span className="brand-badge">Autonomous Ops</span>
          </div>
        </Link>
      </div>

      <nav className="navbar-links">
        {navLinks.map((item) => {
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.badge !== undefined && item.badge !== null && (
                <span className="nav-badge-pill">{item.badge}</span>
              )}
            </Link>
          )
        })}
      </nav>

      <div className="navbar-right">
        {onLogout && (
          <div className="account-controls">
            <span className="account-name">{username || 'Local account'}</span>
            <button
              type="button"
              className="btn-secondary logout-button"
              onClick={() => { setShowPasswordForm((visible) => !visible); setPasswordError('') }}
            >
              Password
            </button>
            <button type="button" className="btn-secondary logout-button" onClick={onLogout}>
              Sign out
            </button>
          </div>
        )}
        <div className="system-status-pill">
          <span className={`status-orb ${isApiOnline ? 'online' : 'offline'}`} />
          <span className="status-meta">
            API: <strong>{isApiOnline ? 'Online' : 'Disconnected'}</strong>
            <span className="meta-sep">·</span>
            ML: <strong className={isModelReady ? 'text-accent' : 'text-warn'}>
              {isModelReady ? 'Isolation Forest' : 'Fallback'}
            </strong>
          </span>
        </div>
      </div>
      {showPasswordForm && onPasswordChanged && (
        <form className="password-popover" onSubmit={handlePasswordSubmit}>
          <strong>Change local password</strong>
          <label htmlFor="currentPassword">Current password</label>
          <input id="currentPassword" name="currentPassword" type="password" autoComplete="current-password" required />
          <label htmlFor="newPassword">New password</label>
          <input id="newPassword" name="newPassword" type="password" autoComplete="new-password" minLength={12} required />
          <label htmlFor="confirmPassword">Confirm new password</label>
          <input id="confirmPassword" name="confirmPassword" type="password" autoComplete="new-password" minLength={12} required />
          {passwordError && <p className="auth-error" role="alert">{passwordError}</p>}
          <button className="btn-primary" type="submit" disabled={passwordSaving}>
            {passwordSaving ? 'Saving…' : 'Save and sign out'}
          </button>
        </form>
      )}
    </header>
  )
}
