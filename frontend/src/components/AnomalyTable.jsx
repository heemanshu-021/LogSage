export default function AnomalyTable({ anomalies, onSelect, selected }) {
  if (!anomalies.length) {
    return (
      <div className="card">
        <h2>🚨 Anomalies</h2>
        <p className="no-data">No anomalies yet. Ingest logs to begin.</p>
      </div>
    )
  }

  const scoreClass = (s) => s >= 0.7 ? 'score-high' : s >= 0.4 ? 'score-mid' : 'score-low'

  return (
    <div className="card">
      <h2>🚨 Anomalies <span style={{ color:'var(--text-muted)', fontWeight:400 }}>({anomalies.length})</span></h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Score</th>
              <th>Label</th>
              <th>Detector</th>
              <th>Detected At</th>
            </tr>
          </thead>
          <tbody>
            {anomalies.map(a => (
              <tr
                key={a.id}
                className={selected?.id === a.id ? 'selected' : ''}
                onClick={() => onSelect(a)}
              >
                <td>#{a.id}</td>
                <td><span className={scoreClass(a.score)}>{a.score.toFixed(3)}</span></td>
                <td>
                  <span className={`badge badge-${a.label}`}>{a.label}</span>
                </td>
                <td style={{ color:'var(--text-muted)' }}>{a.detector}</td>
                <td style={{ color:'var(--text-muted)', fontSize:'0.75rem' }}>
                  {new Date(a.detected_at).toLocaleTimeString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
