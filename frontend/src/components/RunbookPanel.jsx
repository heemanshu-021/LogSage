import { useState } from 'react'

export default function RunbookPanel({
  incident,
  incidentDetail,
  loadingDetail,
  apiUrl,
}) {
  const [customQuery, setCustomQuery] = useState('')
  const [customHits, setCustomHits] = useState(null)
  const [searching, setSearching] = useState(false)

  const handleCustomSearch = async (e) => {
    e.preventDefault()
    if (!customQuery.trim() || customQuery.length < 3) return
    setSearching(true)
    try {
      const res = await fetch(
        `${apiUrl}/api/runbooks/search?q=${encodeURIComponent(customQuery)}&top_k=3`
      )
      if (res.ok) {
        setCustomHits(await res.json())
      } else {
        setCustomHits([])
      }
    } catch {
      setCustomHits([])
    } finally {
      setSearching(false)
    }
  }

  // Active runbooks: either custom search hits (if searched) or recommended from incident
  const displayedRunbooks =
    customHits !== null
      ? customHits
      : incidentDetail?.recommended_runbooks || []

  return (
    <div className="card detail-panel">
      <h2>📖 Triage & Runbook Intelligence</h2>

      {/* Manual Search */}
      <form onSubmit={handleCustomSearch} className="search-input-box">
        <input
          type="text"
          className="search-input"
          placeholder="Search ops runbooks (e.g. HDFS block corrupt)..."
          value={customQuery}
          onChange={(e) => setCustomQuery(e.target.value)}
        />
        <button type="submit" className="btn btn-secondary btn-sm" disabled={searching}>
          {searching ? <span className="spinner" /> : 'Search'}
        </button>
        {customHits !== null && (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setCustomHits(null)}
          >
            Clear
          </button>
        )}
      </form>

      {/* Selected Incident Context */}
      {loadingDetail ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1.5rem 0' }}>
          <div className="spinner" />
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Loading incident evidence & runbook matches...
          </span>
        </div>
      ) : incidentDetail ? (
        <div>
          <div className="incident-card-top">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>SELECTED INCIDENT</div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#fff' }}>
                  {incidentDetail.incident_id}
                </div>
              </div>
              <span className={`badge badge-${(incidentDetail.severity || 'LOW').toLowerCase()}`}>
                {incidentDetail.severity}
              </span>
            </div>

            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
              Block: <strong style={{ fontFamily: 'monospace' }}>{incidentDetail.block_id}</strong> · Score:{' '}
              <strong style={{ color: 'var(--danger)' }}>
                {(incidentDetail.anomaly_score).toFixed(4)}
              </strong>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              {incidentDetail.title}
            </div>
          </div>

          {/* Feature Attribution */}
          {incidentDetail.top_features && incidentDetail.top_features.length > 0 && (
            <div>
              <div className="section-title">Top Contributing Features (Anomaly Attribution)</div>
              <div className="feature-grid">
                {incidentDetail.top_features.map((f, i) => (
                  <div key={i} className="feature-item">
                    <span className="feature-name">{f.feature}</span>
                    <span className="feature-val">{typeof f.value === 'number' ? f.value.toFixed(4) : f.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Raw Log Evidence */}
          {incidentDetail.raw_evidence && incidentDetail.raw_evidence.length > 0 && (
            <div>
              <div className="section-title">Raw Log Evidence</div>
              <div className="evidence-box">
                {incidentDetail.raw_evidence.map((line, idx) => (
                  <div key={idx} className="evidence-line">
                    {line}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : !customHits ? (
        <div className="empty-placeholder">
          <p>👈 Select an incident from the table</p>
          <p style={{ fontSize: '0.78rem', marginTop: '0.4rem' }}>
            To inspect root-cause feature attributions, raw log traces, and automated runbook recommendations.
          </p>
        </div>
      ) : null}

      {/* Runbook Matches */}
      <div className="section-title" style={{ marginTop: '1.25rem' }}>
        {customHits !== null ? 'Search Results' : 'Recommended Ops Runbooks'}
      </div>

      {displayedRunbooks.length === 0 ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic', padding: '0.5rem 0' }}>
          {incidentDetail
            ? 'No automated runbook matches found for this block pattern.'
            : 'No runbooks found for query.'}
        </p>
      ) : (
        displayedRunbooks.map((rb, idx) => (
          <div key={rb.slug || idx} className="runbook-hit">
            <div className="runbook-hit-header">
              <div className="runbook-title">
                <span style={{ color: 'var(--text-muted)', marginRight: '0.35rem' }}>#{idx + 1}</span>
                {rb.title}
              </div>
              {rb.score !== undefined && (
                <span className="runbook-score">
                  {(rb.score * 100).toFixed(0)}% match
                </span>
              )}
            </div>
            <div className="runbook-excerpt">{rb.excerpt}</div>
          </div>
        ))
      )}
    </div>
  )
}
