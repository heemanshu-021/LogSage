export default function RunbookPanel({ anomaly, runbooks, loading }) {
  return (
    <div className="card runbook-panel">
      <h2>📖 Runbook Suggestions</h2>

      {!anomaly && (
        <p className="runbook-empty">Click an anomaly row to retrieve relevant runbooks.</p>
      )}

      {anomaly && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', background:'var(--bg)', borderRadius:'var(--radius)' }}>
          <div style={{ fontSize:'0.75rem', color:'var(--text-muted)' }}>Selected anomaly</div>
          <div>ID #{anomaly.id} · Score <strong style={{ color: anomaly.score >= 0.7 ? 'var(--danger)' : 'var(--warn)' }}>{anomaly.score.toFixed(3)}</strong></div>
          <div style={{ fontSize:'0.8rem', color:'var(--text-muted)' }}>{anomaly.detector}</div>
        </div>
      )}

      {loading && (
        <div style={{ display:'flex', alignItems:'center', gap:'0.75rem', padding:'1rem 0' }}>
          <div className="spinner" />
          <span style={{ color:'var(--text-muted)' }}>Searching runbooks…</span>
        </div>
      )}

      {!loading && anomaly && runbooks.length === 0 && (
        <p className="runbook-empty">No matching runbooks found.</p>
      )}

      {!loading && runbooks.map((rb, i) => (
        <div key={rb.slug} className="runbook-hit">
          <div className="runbook-title">
            <span style={{ color:'var(--text-muted)', marginRight:'0.4rem' }}>#{i+1}</span>
            {rb.title}
          </div>
          <div className="runbook-score">
            Similarity: {(rb.score * 100).toFixed(1)}%
          </div>
          <div className="runbook-excerpt">{rb.excerpt}</div>
        </div>
      ))}
    </div>
  )
}
