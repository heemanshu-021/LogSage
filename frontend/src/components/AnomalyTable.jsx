export default function AnomalyTable({
  incidents,
  onSelect,
  selected,
  severityFilter,
  setSeverityFilter,
  statusFilter,
  setStatusFilter,
  loading,
}) {
  const getSeverityBadge = (sev) => {
    const s = (sev || 'LOW').toLowerCase()
    return `badge badge-${s}`
  }

  const getScoreClass = (score) => {
    if (score >= 0.85) return 'score-critical'
    if (score >= 0.65) return 'score-high'
    if (score >= 0.45) return 'score-medium'
    return 'score-low'
  }

  const getStatusBadge = (st) => {
    const s = (st || 'OPEN').toLowerCase()
    return `badge badge-${s}`
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>
          🚨 Flagged Incidents{' '}
          <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>
            ({incidents.length})
          </span>
        </h2>

        <div className="filter-bar">
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Severity:</label>
          <select
            className="filter-select"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>

          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status:</label>
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
          <span className="spinner" />
        </div>
      ) : !incidents.length ? (
        <div className="no-data">
          <p>No incidents found matching current filters.</p>
          <p style={{ fontSize: '0.78rem', marginTop: '0.4rem' }}>
            Upload a log file or paste logs to run the Drain3 + Isolation Forest pipeline.
          </p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Incident ID</th>
                <th>Block ID</th>
                <th>Severity</th>
                <th>Anomaly Score</th>
                <th>Events</th>
                <th>Status</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc) => {
                const isSelected = selected?.incident_id === inc.incident_id
                return (
                  <tr
                    key={inc.incident_id}
                    className={isSelected ? 'selected' : ''}
                    onClick={() => onSelect(inc)}
                  >
                    <td style={{ fontWeight: 600, color: 'var(--accent-light)' }}>
                      {inc.incident_id}
                    </td>
                    <td style={{ fontFamily: 'monospace' }}>{inc.block_id}</td>
                    <td>
                      <span className={getSeverityBadge(inc.severity)}>
                        {inc.severity}
                      </span>
                    </td>
                    <td>
                      <span className={getScoreClass(inc.anomaly_score)}>
                        {(inc.anomaly_score).toFixed(4)}
                      </span>
                    </td>
                    <td>{inc.event_count}</td>
                    <td>
                      <span className={getStatusBadge(inc.status)}>
                        {inc.status}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {new Date(inc.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
