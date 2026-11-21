import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import OverviewPage from './pages/OverviewPage'
import ScanPage from './pages/ScanPage'
import IncidentsPage from './pages/IncidentsPage'
import TriagePage from './pages/TriagePage'
import RunbooksPage from './pages/RunbooksPage'
import LoginPage from './pages/LoginPage'
import { apiFetch } from './lib/api'
import './App.css'

export default function App() {
  const [incidents, setIncidents] = useState(null)
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [health, setHealth] = useState({ status: 'checking', ml_model_loaded: false })
  const [auth, setAuth] = useState(null)

  const API = import.meta.env.VITE_API_URL || ''

  const fetchAuth = useCallback(async () => {
    try {
      const response = await apiFetch(`${API}/api/auth/session`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      setAuth(await response.json())
    } catch {
      setAuth({ auth_required: true, authenticated: false, unavailable: true })
    }
  }, [API])

  // Fetch health check
  const fetchHealth = useCallback(async () => {
    try {
      const res = await apiFetch(`${API}/api/health`)
      if (res.ok) {
        setHealth(await res.json())
      } else {
        setHealth({ status: 'error', ml_model_loaded: false })
      }
    } catch {
      setHealth({ status: 'disconnected', ml_model_loaded: false })
    }
  }, [API])

  // Fetch dashboard metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const res = await apiFetch(`${API}/api/dashboard/metrics`)
      if (res.ok) {
        setMetrics(await res.json())
      }
    } catch {
      // background fail-soft
    }
  }, [API])

  // Fetch incidents list
  const fetchIncidents = useCallback(async () => {
    try {
      const res = await apiFetch(`${API}/api/incidents?limit=100`)
      if (res.ok) {
        const data = await res.json()
        const list = data.incidents || []
        setIncidents(list)
        if (list.length > 0) setSelectedIncident((current) => current || list[0])
      } else {
        setIncidents((current) => current ?? [])
      }
    } catch (err) {
      console.error('Failed to fetch incidents', err)
      setIncidents((current) => current ?? [])
    }
  }, [API])

  useEffect(() => {
    let active = true
    queueMicrotask(() => {
      if (active) fetchAuth()
    })
    return () => { active = false }
  }, [fetchAuth])

  // Load dashboard data only after the local session has been checked.
  useEffect(() => {
    if (!auth?.authenticated) return
    let active = true
    queueMicrotask(() => {
      if (!active) return
      fetchHealth()
      fetchMetrics()
      fetchIncidents()
    })
    return () => { active = false }
  }, [auth?.authenticated, fetchHealth, fetchMetrics, fetchIncidents])

  // Periodic polling every 12 seconds
  useEffect(() => {
    if (!auth?.authenticated) return undefined
    const timer = setInterval(() => {
      fetchHealth()
      fetchMetrics()
      fetchIncidents()
    }, 12000)
    return () => clearInterval(timer)
  }, [auth?.authenticated, fetchHealth, fetchMetrics, fetchIncidents])

  // Callback after successful scan
  const handleAnalysisSuccess = (result) => {
    fetchMetrics()
    fetchIncidents()
    if (result.incidents && result.incidents.length > 0) {
      setSelectedIncident(result.incidents[0])
    }
  }

  const handleLogout = async () => {
    try {
      const response = await apiFetch(`${API}/api/auth/logout`, { method: 'POST' })
      if (!response.ok) throw new Error(`Sign-out failed (HTTP ${response.status})`)
      setAuth({ auth_required: true, authenticated: false })
      setIncidents(null)
      setSelectedIncident(null)
      setMetrics(null)
    } catch (error) {
      console.error('Failed to sign out', error)
    }
  }

  const handlePasswordChanged = () => {
    setAuth({ auth_required: true, authenticated: false })
    setIncidents(null)
    setSelectedIncident(null)
    setMetrics(null)
  }

  if (auth === null) {
    return <main className="auth-screen"><p className="page-desc">Connecting to LogSage…</p></main>
  }

  if (auth.auth_required && !auth.authenticated) {
    return (
      <LoginPage
        apiUrl={API}
        unavailable={auth.unavailable}
        onRetry={fetchAuth}
        onLogin={(username) => setAuth({ auth_required: true, authenticated: true, username })}
      />
    )
  }

  const incidentList = incidents ?? []
  const loadingIncidents = incidents === null
  const openIncidentsCount = incidentList.filter((i) => i.status === 'OPEN').length

  return (
    <BrowserRouter>
      <div className="app-root">
        {/* Top Navbar */}
        <Navbar
          health={health}
          openIncidentsCount={openIncidentsCount}
          username={auth.username}
          onLogout={auth.auth_required ? handleLogout : undefined}
          onPasswordChanged={auth.auth_required ? handlePasswordChanged : undefined}
        />

        {/* Ambient background glows */}
        <div className="ambient-glow glow-1" />
        <div className="ambient-glow glow-2" />

        {/* Main Routed Content */}
        <main className="content-container">
          <Routes>
            <Route
              path="/"
              element={
                <OverviewPage
                  metrics={metrics}
                  incidents={incidentList}
                  health={health}
                  onSelectIncident={(inc) => setSelectedIncident(inc)}
                />
              }
            />
            <Route
              path="/scan"
              element={
                <ScanPage
                  apiUrl={API}
                  onAnalysisSuccess={handleAnalysisSuccess}
                />
              }
            />
            <Route
              path="/incidents"
              element={
                <IncidentsPage
                  incidents={incidentList}
                  loading={loadingIncidents}
                  onSelectIncident={(inc) => setSelectedIncident(inc)}
                  selectedIncident={selectedIncident}
                />
              }
            />
            <Route
              path="/triage"
              element={
                <TriagePage
                  apiUrl={API}
                  incidents={incidentList}
                  selectedIncident={selectedIncident}
                  onSelectIncident={(inc) => setSelectedIncident(inc)}
                />
              }
            />
            <Route
              path="/runbooks"
              element={<RunbooksPage apiUrl={API} />}
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="footer">
          <div className="footer-content">
            <span>🛡️ LogSage Autonomous Ops Engine · Drain3 + Isolation Forest + FAISS</span>
            <span className="footer-sub">Logfit HDFS_v1 Held-Out: 76.2% Precision · 86.6% Recall</span>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}
