import { useState, useEffect, useCallback } from 'react'
import LogUpload from './components/LogUpload'
import AnomalyTable from './components/AnomalyTable'
import RunbookPanel from './components/RunbookPanel'
import StatusBar from './components/StatusBar'
import './App.css'

function App() {
  const [incidents, setIncidents] = useState([])
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [incidentDetail, setIncidentDetail] = useState(null)
  const [loadingIncidents, setLoadingIncidents] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [metrics, setMetrics] = useState(null)
  const [health, setHealth] = useState({ status: 'checking', ml_model_loaded: false })
  const [status, setStatus] = useState({ type: 'idle', message: 'System Ready' })
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState('ALL')

  const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Fetch health check
  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/health`)
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
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
      const res = await fetch(`${API}/api/dashboard/metrics`)
      if (res.ok) {
        setMetrics(await res.json())
      }
    } catch {
      // ignore in background
    }
  }, [API])

  // Fetch incidents list with active filters
  const fetchIncidents = useCallback(async () => {
    setLoadingIncidents(true)
    try {
      const params = new URLSearchParams({ limit: '100', offset: '0' })
      if (severityFilter !== 'ALL') params.append('severity', severityFilter)
      if (statusFilter !== 'ALL') params.append('status', statusFilter)

      const res = await fetch(`${API}/api/incidents?${params.toString()}`)
      if (res.ok) {
        const data = await res.json()
        setIncidents(data.incidents || [])
      }
    } catch (err) {
      console.error('Failed to fetch incidents', err)
    } finally {
      setLoadingIncidents(false)
    }
  }, [API, severityFilter, statusFilter])

  // Initial load
  useEffect(() => {
    fetchHealth()
    fetchMetrics()
    fetchIncidents()
  }, [fetchHealth, fetchMetrics, fetchIncidents])

  // Periodic poll for metrics every 15s
  useEffect(() => {
    const timer = setInterval(() => {
      fetchMetrics()
      fetchHealth()
    }, 15000)
    return () => clearInterval(timer)
  }, [fetchMetrics, fetchHealth])

  // Select incident and load detail
  const handleSelectIncident = async (inc) => {
    setSelectedIncident(inc)
    setLoadingDetail(true)
    try {
      const res = await fetch(`${API}/api/incidents/${inc.incident_id}`)
      if (res.ok) {
        setIncidentDetail(await res.json())
      } else {
        setIncidentDetail(null)
      }
    } catch {
      setIncidentDetail(null)
    } finally {
      setLoadingDetail(false)
    }
  }

  // Handle analysis complete
  const handleIngestComplete = (result) => {
    setStatus({
      type: 'success',
      message: `Parsed ${result.total_lines} lines across ${result.total_blocks} blocks. Flagged ${result.anomalous_blocks} anomalous blocks in ${result.processing_time_ms.toFixed(1)}ms.`,
    })
    fetchMetrics()
    fetchIncidents()

    // If new incidents were created, auto-select the first one
    if (result.incidents && result.incidents.length > 0) {
      handleSelectIncident(result.incidents[0])
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="logo">🛡️ LogSage</h1>
          <p className="tagline">Log Anomaly Detection with Runbook-Retrieval Triage</p>
        </div>
        <div className="system-pill">
          <span
            className={`pill-dot ${health.status === 'ok' ? '' : 'error'}`}
          />
          <span>
            API: <strong>{health.status}</strong> · Model:{' '}
            <strong>{health.ml_model_loaded ? 'Loaded (IForest)' : 'Fallback'}</strong>
          </span>
        </div>
      </header>

      {/* Real-time Dashboard Metrics Bar */}
      {metrics && (
        <section className="metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Logs Ingested</span>
            <span className="metric-value">{metrics.total_logs_ingested.toLocaleString()}</span>
            <span className="metric-sub">Total lines recorded</span>
          </div>

          <div className="metric-card">
            <span className="metric-label">Blocks Evaluated</span>
            <span className="metric-value">{metrics.total_blocks_analyzed.toLocaleString()}</span>
            <span className="metric-sub">Aggregated HDFS traces</span>
          </div>

          <div className="metric-card">
            <span className="metric-label">Flagged Incidents</span>
            <span className="metric-value" style={{ color: 'var(--danger)' }}>
              {metrics.total_incidents.toLocaleString()}
            </span>
            <span className="metric-sub">
              {metrics.open_incidents} currently open
            </span>
          </div>

          <div className="metric-card">
            <span className="metric-label">Anomaly Rate</span>
            <span className="metric-value" style={{ color: 'var(--warn)' }}>
              {metrics.anomaly_rate_percent.toFixed(2)}%
            </span>
            <span className="metric-sub">Based on empirical threshold</span>
          </div>
        </section>
      )}

      {/* Main Grid */}
      <main className="main">
        {/* Left Column: Ingestion + Incidents Table */}
        <div className="col-left">
          <LogUpload
            apiUrl={API}
            onStart={() => setStatus({ type: 'loading', message: 'Uploading and processing log stream...' })}
            onComplete={handleIngestComplete}
            onError={(msg) => setStatus({ type: 'error', message: msg })}
          />

          <StatusBar status={status} />

          <AnomalyTable
            incidents={incidents}
            selected={selectedIncident}
            onSelect={handleSelectIncident}
            severityFilter={severityFilter}
            setSeverityFilter={setSeverityFilter}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            loading={loadingIncidents}
          />
        </div>

        {/* Right Column: Runbook & Triage Intelligence */}
        <div className="col-right">
          <RunbookPanel
            incident={selectedIncident}
            incidentDetail={incidentDetail}
            loadingDetail={loadingDetail}
            apiUrl={API}
          />
        </div>
      </main>
    </div>
  )
}

export default App
