import { useState } from 'react'
import { apiFetch } from '../lib/api'

export default function LoginPage({ apiUrl, onLogin, unavailable, onRetry }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const response = await apiFetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const body = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(body.detail || `Sign-in failed (HTTP ${response.status})`)
      setPassword('')
      onLogin(body.username)
    } catch (err) {
      setError(err.message || 'Could not sign in. Check the local API connection.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-screen">
      <div className="ambient-glow glow-1" />
      <div className="ambient-glow glow-2" />
      <section className="glass-card auth-card" aria-labelledby="login-title">
        <div className="auth-brand-mark" aria-hidden="true">🛡️</div>
        <span className="page-tag">LOCAL ACCOUNT</span>
        <h1 id="login-title" className="page-title">Sign in to LogSage</h1>
        <p className="page-desc">Use the local account configured for this LogSage instance.</p>
        {unavailable && (
          <div className="auth-error" role="alert">
            LogSage could not be reached. Check that the local service is running, then{' '}
            <button type="button" className="auth-retry" onClick={onRetry}>try again</button>.
          </div>
        )}
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
            maxLength={128}
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            maxLength={1024}
          />
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="btn-primary auth-submit" type="submit" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  )
}
