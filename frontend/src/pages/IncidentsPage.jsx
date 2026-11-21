import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

export default function IncidentsPage({
  incidents,
  loading,
  onSelectIncident,
  selectedIncident,
}) {
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const navigate = useNavigate()

  const filteredIncidents = useMemo(() => {
    return incidents.filter((inc) => {
      // Severity check
      if (severityFilter !== 'ALL' && inc.severity !== severityFilter) {
        return false
      }
      // Status check
      if (statusFilter !== 'ALL' && inc.status !== statusFilter) {
        return false
      }
      // Search query check
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const matchesId = inc.incident_id?.toLowerCase().includes(q)
        const matchesBlock = inc.block_id?.toLowerCase().includes(q)
        const matchesTitle = inc.title?.toLowerCase().includes(q)
        if (!matchesId && !matchesBlock && !matchesTitle) return false
      }
      return true
    })
  }, [incidents, severityFilter, statusFilter, searchQuery])

  const handleOpenTriage = (inc) => {
    if (onSelectIncident) onSelectIncident(inc)
    navigate('/triage')
  }

  const getScoreColor = (score) => {
    if (score >= 0.85) return 'text-danger'
    if (score >= 0.65) return 'text-warn'
    if (score >= 0.45) return 'text-info'
    return 'text-ok'
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <span className="page-tag">INCIDENT TRIAGE CENTER</span>
          <h1 className="page-title">Flagged Incidents</h1>
          <p className="page-desc">
            Anomalous block traces identified by the Isolation Forest model. Select any incident
            to inspect root-cause feature attributions and execute recovery runbooks.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-card filter-card">
        <div className="filter-row">
          {/* Search Input */}
          <div className="search-box">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="search-input-field"
              placeholder="Search by block ID, incident ID, or title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                className="clear-search-btn"
                onClick={() => setSearchQuery('')}
              >
                ✕
              </button>
            )}
          </div>

          {/* Severity Pills */}
          <div className="pill-group">
            <span className="pill-group-label">Severity:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                className={`filter-pill ${severityFilter === sev ? 'active' : ''}`}
                onClick={() => setSeverityFilter(sev)}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Status Pills */}
          <div className="pill-group">
            <span className="pill-group-label">Status:</span>
            {['ALL', 'OPEN', 'INVESTIGATING', 'RESOLVED'].map((st) => (
              <button
                key={st}
                className={`filter-pill ${statusFilter === st ? 'active' : ''}`}
                onClick={() => setStatusFilter(st)}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Incidents Table / Card Grid */}
      {loading ? (
        <div className="loading-state-box glass-card">
          <div className="spinner" />
          <p>Loading incidents from database...</p>
        </div>
      ) : filteredIncidents.length === 0 ? (
        <div className="empty-state-box glass-card">
          <div className="empty-icon">🛡️</div>
          <h3>No Incidents Found</h3>
          <p>
            {incidents.length === 0
              ? 'No log anomalies have been detected yet. Run a log scan to analyze server activity.'
              : 'No incidents match your current search and severity filters.'}
          </p>
          {incidents.length === 0 && (
            <button className="btn btn-primary" onClick={() => navigate('/scan')}>
              Scan Log Files ➔
            </button>
          )}
        </div>
      ) : (
        <div className="glass-card table-card">
          <div className="table-responsive">
            <table className="incidents-table">
              <thead>
                <tr>
                  <th>INCIDENT ID</th>
                  <th>BLOCK ID</th>
                  <th>TITLE & SYMPTOMS</th>
                  <th>SEVERITY</th>
                  <th>SCORE</th>
                  <th>EVENTS</th>
                  <th>STATUS</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {filteredIncidents.map((inc) => {
                  const isSelected = selectedIncident?.incident_id === inc.incident_id
                  return (
                    <tr
                      key={inc.incident_id}
                      className={isSelected ? 'row-selected' : ''}
                    >
                      <td>
                        <span className="incident-id-badge">{inc.incident_id}</span>
                      </td>
                      <td>
                        <code className="block-code">{inc.block_id}</code>
                      </td>
                      <td>
                        <div className="incident-title-cell">
                          <span className="inc-main-title">{inc.title}</span>
                          <span className="inc-timestamp">
                            {new Date(inc.created_at).toLocaleString()}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge badge-${(inc.severity || 'LOW').toLowerCase()}`}>
                          {inc.severity}
                        </span>
                      </td>
                      <td>
                        <div className="score-cell">
                          <span className={`score-value ${getScoreColor(inc.anomaly_score)}`}>
                            {(inc.anomaly_score).toFixed(4)}
                          </span>
                          <div className="score-mini-bar">
                            <div
                              className="score-mini-fill"
                              style={{ width: `${Math.min(100, inc.anomaly_score * 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="events-count">{inc.event_count} lines</span>
                      </td>
                      <td>
                        <span className={`badge badge-${(inc.status || 'OPEN').toLowerCase()}`}>
                          {inc.status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-primary btn-sm triage-btn"
                          onClick={() => handleOpenTriage(inc)}
                        >
                          Triage ➔
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
