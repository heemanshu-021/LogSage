import { Link, useNavigate } from 'react-router-dom'

export default function OverviewPage({ metrics, incidents, health, onSelectIncident }) {
  const navigate = useNavigate()

  const handleIncidentClick = (inc) => {
    if (onSelectIncident) onSelectIncident(inc)
    navigate('/triage')
  }

  const totalLogs = metrics?.total_logs_ingested ?? 0
  const totalBlocks = metrics?.total_blocks_analyzed ?? 0
  const totalIncidents = metrics?.total_incidents ?? incidents.length
  const openIncidents = metrics?.open_incidents ?? incidents.filter(i => i.status === 'OPEN').length
  return (
    <div className="page-container">
      {/* Hero Header */}
      <section className="hero-header">
        <div className="hero-badge-container">
          <span className="hero-pill">⚡ Powered by Drain3 + Isolation Forest + FAISS</span>
        </div>
        <h1 className="hero-title">
          Autonomous Log Anomaly Detection <br />
          <span className="hero-gradient-text">& Instant Runbook Triage</span>
        </h1>
        <p className="hero-subtitle">
          LogSage turns hundreds of thousands of noisy server logs into pinpointed root-cause
          diagnostics and step-by-step CLI recovery commands in milliseconds.
        </p>

        <div className="hero-actions">
          <Link to="/scan" className="btn btn-primary btn-lg">
            <span>📥 Scan New Logs</span>
            <span className="arrow-icon">➔</span>
          </Link>
          <Link to="/incidents" className="btn btn-glass btn-lg">
            <span>🚨 View Incidents ({openIncidents})</span>
          </Link>
        </div>
      </section>

      {/* Apple-Style Bento Grid */}
      <section className="bento-grid">
        {/* Bento Tile 1 (Large 2x2): System & Detection Engine Pulse */}
        <div className="bento-tile bento-large glass-card">
          <div className="tile-header">
            <span className="tile-tag">AI INFERENCE ENGINE</span>
            <span className="status-live-tag">● LIVE INFERENCE</span>
          </div>

          <div className="engine-pulse-body">
            <div className="pulse-graphic">
              <div className="pulse-ring ring-1" />
              <div className="pulse-ring ring-2" />
              <div className="pulse-core">🛡️</div>
            </div>

            <div className="engine-details">
              <h3>Drain3 + Isolation Forest Pipeline</h3>
              <p>
                Online streaming template parser with regex masking (depth=4, sim_th=0.5)
                streaming directly into a 150-estimator Isolation Forest calibrated with empirical prior contamination.
              </p>

              <div className="engine-stats-grid">
                <div className="engine-stat-item">
                  <span className="stat-label">PARSER DEPTH</span>
                  <span className="stat-value">4 Layers</span>
                </div>
                <div className="engine-stat-item">
                  <span className="stat-label">ESTIMATORS</span>
                  <span className="stat-value">150 Trees</span>
                </div>
                <div className="engine-stat-item">
                  <span className="stat-label">TRAIN CONTAMINATION</span>
                  <span className="stat-value">2.92%</span>
                </div>
                <div className="engine-stat-item">
                  <span className="stat-label">STATUS</span>
                  <span className="stat-value text-accent">
                    {health?.ml_model_loaded ? 'Active' : 'Standby'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bento Tile 2 (1x1): Logfit HDFS_v1 held-out precision */}
        <div className="bento-tile bento-stat glass-card glow-blue">
          <span className="tile-tag">LOGFIT HDFS_V1 · HELD-OUT</span>
          <div className="stat-big-number">76.2%</div>
          <div className="stat-big-label">Precision Rate</div>
          <p className="stat-micro-desc">At the validation-selected cutoff across 114,803 blocks; recall was 86.6%.</p>
        </div>

        {/* Bento Tile 3 (1x1): Active Incidents */}
        <div className="bento-tile bento-stat glass-card glow-red">
          <span className="tile-tag">ATTENTION REQUIRED</span>
          <div className="stat-big-number text-danger">{openIncidents}</div>
          <div className="stat-big-label">Open Incidents</div>
          <p className="stat-micro-desc">
            {openIncidents > 0 ? 'Requires on-call triage' : 'All systems operating normally'}
          </p>
        </div>

        {/* Bento Tile 4 (1x1): Total Logs Ingested */}
        <div className="bento-tile bento-stat glass-card">
          <span className="tile-tag">THROUGHPUT</span>
          <div className="stat-big-number">{totalLogs.toLocaleString()}</div>
          <div className="stat-big-label">Logs Processed</div>
          <p className="stat-micro-desc">Raw log messages structured & tokenized.</p>
        </div>

        {/* Bento Tile 5 (1x1): Blocks Analyzed */}
        <div className="bento-tile bento-stat glass-card">
          <span className="tile-tag">AGGREGATION</span>
          <div className="stat-big-number">{totalBlocks.toLocaleString()}</div>
          <div className="stat-big-label">Block Traces</div>
          <p className="stat-micro-desc">Correlated lifecycle traces analyzed.</p>
        </div>

        {/* Bento Tile 6 (Wide 2x1): Fast Scan Launchpad */}
        <div className="bento-tile bento-wide glass-card">
          <div className="tile-header">
            <span className="tile-tag">FAST LOG INGESTION</span>
            <Link to="/scan" className="tile-link">Open Full Scanner ➔</Link>
          </div>
          <div className="quick-scan-content">
            <div className="quick-scan-desc">
              <h4>Drop or paste a server log trace to trigger instant triage</h4>
              <p>Supports HDFS, Syslog, Apache, and custom enterprise log files up to 25 MB.</p>
            </div>
            <Link to="/scan" className="btn btn-primary btn-sm">
              Launch Scanner
            </Link>
          </div>
        </div>

        {/* Bento Tile 7 (Wide 2x1): Recent Flagged Incidents */}
        <div className="bento-tile bento-wide glass-card">
          <div className="tile-header">
            <span className="tile-tag">RECENT INCIDENTS</span>
            <Link to="/incidents" className="tile-link">View All ({totalIncidents}) ➔</Link>
          </div>

          <div className="recent-incidents-list">
            {!incidents || incidents.length === 0 ? (
              <div className="empty-subtext">No incidents recorded yet. Run a scan to evaluate logs.</div>
            ) : (
              incidents.slice(0, 3).map((inc) => (
                <div
                  key={inc.incident_id}
                  className="recent-inc-row"
                  onClick={() => handleIncidentClick(inc)}
                >
                  <div className="inc-row-left">
                    <span className={`badge badge-${(inc.severity || 'LOW').toLowerCase()}`}>
                      {inc.severity}
                    </span>
                    <span className="inc-id-tag">{inc.incident_id}</span>
                    <span className="inc-block-tag">{inc.block_id}</span>
                  </div>
                  <div className="inc-row-right">
                    <span className="inc-score">Score: {(inc.anomaly_score).toFixed(3)}</span>
                    <span className="solve-cta">Solve ➔</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
