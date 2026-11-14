import { useState, useEffect } from 'react'
import LogUpload from './components/LogUpload'
import AnomalyTable from './components/AnomalyTable'
import RunbookPanel from './components/RunbookPanel'
import StatusBar from './components/StatusBar'
import './App.css'

function App() {
  const [anomalies, setAnomalies] = useState([])
  const [runbooks, setRunbooks] = useState([])
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ type: 'idle', message: 'Ready' })

  const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const fetchAnomalies = async () => {
    try {
      const res = await fetch(`${API}/anomalies?limit=100`)
      if (res.ok) setAnomalies(await res.json())
    } catch {
      console.error('Failed to fetch anomalies')
    }
  }

  useEffect(() => { fetchAnomalies() }, [])

  const handleIngestComplete = (result) => {
    setStatus({
      type: 'success',
      message: `Ingested ${result.accepted} lines • ${result.anomalies_detected} anomalies detected`
    })
    fetchAnomalies()
  }

  const handleSelectAnomaly = async (anomaly) => {
    setSelectedAnomaly(anomaly)
    setLoading(true)
    try {
      const query = `anomaly score ${anomaly.score.toFixed(2)} detected by ${anomaly.detector}`
      const res = await fetch(`${API}/runbooks/search?q=${encodeURIComponent(query)}&top_k=3`)
      if (res.ok) setRunbooks(await res.json())
    } catch {
      setRunbooks([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1 className="logo">🔍 LogSage</h1>
          <p className="tagline">Log Anomaly Detection · Runbook-Retrieval Triage</p>
        </div>
      </header>

      <main className="main">
        <div className="col-left">
          <LogUpload
            apiUrl={API}
            onComplete={handleIngestComplete}
            onError={(msg) => setStatus({ type: 'error', message: msg })}
          />
          <StatusBar status={status} />
          <AnomalyTable
            anomalies={anomalies}
            onSelect={handleSelectAnomaly}
            selected={selectedAnomaly}
          />
        </div>

        <div className="col-right">
          <RunbookPanel
            anomaly={selectedAnomaly}
            runbooks={runbooks}
            loading={loading}
          />
        </div>
      </main>
    </div>
  )
}

export default App
