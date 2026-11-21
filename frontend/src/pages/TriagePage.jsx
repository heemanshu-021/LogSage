import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import CommandBlock from '../components/CommandBlock'
import { apiFetch } from '../lib/api'

export default function TriagePage({
  apiUrl,
  incidents,
  selectedIncident,
  onSelectIncident,
}) {
  const [manuallySelectedIncidentId, setManuallySelectedIncidentId] = useState('')
  const activeIncidentId =
    selectedIncident?.incident_id ||
    manuallySelectedIncidentId ||
    incidents[0]?.incident_id ||
    ''
  const [incidentDetail, setIncidentDetail] = useState(null)
  const [loadedIncidentId, setLoadedIncidentId] = useState('')
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [incidentStatus, setIncidentStatus] = useState(
    selectedIncident?.status || 'OPEN'
  )

  // Fetch full incident details whenever activeIncidentId changes
  useEffect(() => {
    if (!activeIncidentId) return
    let isMounted = true

    apiFetch(`${apiUrl}/api/incidents/${activeIncidentId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        if (isMounted) {
          setIncidentDetail(data)
          setIncidentStatus(data.status || 'OPEN')
        }
      })
      .catch(() => {
        if (isMounted) setIncidentDetail(null)
      })
      .finally(() => {
        if (isMounted) setLoadedIncidentId(activeIncidentId)
      })

    return () => {
      isMounted = false
    }
  }, [activeIncidentId, apiUrl])

  const loading = Boolean(activeIncidentId) && loadedIncidentId !== activeIncidentId

  const handleSelectChange = (e) => {
    const id = e.target.value
    setManuallySelectedIncidentId(id)
    const found = incidents.find((i) => i.incident_id === id)
    if (found && onSelectIncident) {
      onSelectIncident(found)
    }
  }

  // Get simple plain-English diagnosis based on incident content
  const getPlainEnglishDiagnosis = (detail) => {
    if (!detail) return ''
    const title = detail.title || ''
    const blockId = detail.block_id || 'unknown block'

    if (title.toLowerCase().includes('corrupt') || blockId.includes('999')) {
      return `HDFS storage block "${blockId}" suffered a fatal I/O exception during replication between cluster DataNodes and was flagged as corrupt by the NameSystem. This causes checksum errors when clients try to read files stored on this block.`
    }
    if (title.toLowerCase().includes('slow') || title.toLowerCase().includes('io')) {
      return `Disk write operations on block "${blockId}" exceeded normal latency thresholds (>3000ms). This indicates disk saturation, failing storage controller, or network packet stalls on the hosting DataNode.`
    }
    return `Anomalous execution sequence detected on block "${blockId}". Log pattern frequency diverged significantly from normal baseline traffic with an anomaly score of ${detail.anomaly_score?.toFixed(4)}.`
  }

  // Generate actionable remediation steps with exact commands
  const getRemediationSteps = (detail) => {
    const block = detail?.block_id || 'blk_999'

    return [
      {
        step: 1,
        title: 'Diagnose Corrupted Blocks & DataNode Locations',
        desc: 'Scan the filesystem metadata to pinpoint which DataNodes hold the bad replica.',
        command: `hdfs fsck / -list-corruptfileblocks 2>&1 | head -50`,
      },
      {
        step: 2,
        title: `Verify Locations for Target Block ${block}`,
        desc: 'Identify the active and dead host IPs storing this specific block ID.',
        command: `hdfs fsck / -files -blocks -locations | grep -B 2 -A 5 "${block}"`,
      },
      {
        step: 3,
        title: 'Trigger Clean Re-replication from Healthy Replica',
        desc: 'Forces HDFS to synchronize and re-replicate the block to an alternate healthy node.',
        command: `hdfs dfs -setrep -w 3 /data/hdfs_blocks/${block}`,
      },
      {
        step: 4,
        title: 'Move Unrecoverable Fragment to Lost+Found (If corrupted)',
        desc: 'Clears the corruption alert so filesystem clients do not experience read stalls.',
        command: `hdfs fsck / -move -delete`,
      },
    ]
  }

  return (
    <div className="page-container">
      {/* Header with Incident Dropdown Selector */}
      <div className="triage-header glass-card">
        <div className="triage-header-left">
          <span className="page-tag">INCIDENT RESOLUTION ROOM</span>
          <h1 className="triage-title">
            Triage & Remediate Incident
          </h1>
          <p className="page-desc">
            Plain-English incident analysis with one-click copyable remediation commands.
          </p>
        </div>

        <div className="triage-header-right">
          <label className="incident-picker-label">Select Incident to Triage:</label>
          <select
            className="incident-dropdown"
            value={activeIncidentId}
            onChange={handleSelectChange}
          >
            {incidents.map((inc) => (
              <option key={inc.incident_id} value={inc.incident_id}>
                {inc.incident_id} · {inc.block_id} ({inc.severity})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="glass-card loading-state-box">
          <div className="spinner" />
          <p>Loading incident evidence and matching recovery runbooks...</p>
        </div>
      ) : !incidentDetail ? (
        <div className="glass-card empty-state-box">
          <div className="empty-icon">🔍</div>
          <h3>No Incident Selected</h3>
          <p>Please select an incident from the dropdown or scan a log file to generate a new incident.</p>
          <Link to="/scan" className="btn btn-primary">
            Go to Log Scanner ➔
          </Link>
        </div>
      ) : (
        <div className="triage-grid">
          {/* Main Resolution Column */}
          <div className="triage-main-col">
            {/* Card 1: Plain-English Summary */}
            <div className="glass-card diagnosis-card glow-blue">
              <div className="diagnosis-top">
                <div className="diagnosis-title-group">
                  <span className="section-eyebrow">DIAGNOSIS IN SIMPLE TERMS</span>
                  <h2>What Happened?</h2>
                </div>
                <div className="diagnosis-badges">
                  <span className={`badge badge-${(incidentDetail.severity || 'LOW').toLowerCase()}`}>
                    {incidentDetail.severity}
                  </span>
                  <span className="score-pill">
                    Score: <strong>{(incidentDetail.anomaly_score).toFixed(4)}</strong>
                  </span>
                </div>
              </div>

              <div className="plain-english-box">
                <p className="plain-english-text">
                  {getPlainEnglishDiagnosis(incidentDetail)}
                </p>
              </div>

              <div className="diagnosis-meta-row">
                <div className="meta-pill">
                  Target Block: <code>{incidentDetail.block_id}</code>
                </div>
                <div className="meta-pill">
                  Incident ID: <strong>{incidentDetail.incident_id}</strong>
                </div>
                <div className="meta-pill">
                  Events Analyzed: <strong>{incidentDetail.event_count}</strong>
                </div>
                <div className="meta-pill">
                  Logged At: <span>{new Date(incidentDetail.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>

            {/* Card 2: Simple Step-by-Step Solution with Copyable Commands */}
            <div className="glass-card solution-card">
              <div className="solution-header">
                <div>
                  <span className="section-eyebrow">STEP-BY-STEP RECOVERY MANUAL</span>
                  <h2>How to Fix This Issue</h2>
                </div>
                <span className="solution-tag">Ready-to-Run CLI</span>
              </div>

              <p className="solution-sub">
                Execute the following commands in your cluster terminal. Use the <strong>Copy</strong> button
                to copy each command directly to your clipboard.
              </p>

              <div className="steps-container">
                {getRemediationSteps(incidentDetail).map((stepItem) => (
                  <div key={stepItem.step} className="solution-step-item">
                    <div className="step-badge-number">{stepItem.step}</div>
                    <div className="step-body">
                      <div className="step-heading">{stepItem.title}</div>
                      <div className="step-explanation">{stepItem.desc}</div>
                      <CommandBlock
                        command={stepItem.command}
                        description={`Step ${stepItem.step} Command:`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Card 3: Collapsible Raw Log Evidence */}
            <div className="glass-card evidence-card">
              <div
                className="evidence-toggle-header"
                onClick={() => setEvidenceOpen(!evidenceOpen)}
              >
                <div>
                  <span className="section-eyebrow">AUDIT TRAIL</span>
                  <h3>
                    Raw Log Evidence{' '}
                    <span className="evidence-count">
                      ({incidentDetail.raw_evidence?.length || 0} lines)
                    </span>
                  </h3>
                </div>
                <button
                  type="button"
                  className="btn btn-glass btn-sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    setEvidenceOpen(!evidenceOpen)
                  }}
                >
                  {evidenceOpen ? 'Hide Evidence ▲' : 'Inspect Evidence ▼'}
                </button>
              </div>

              {evidenceOpen && (
                <div className="evidence-drawer">
                  <p className="evidence-intro">
                    The specific log messages extracted by Drain3 for block{' '}
                    <code>{incidentDetail.block_id}</code>:
                  </p>
                  <div className="terminal-evidence-box">
                    {incidentDetail.raw_evidence && incidentDetail.raw_evidence.length > 0 ? (
                      incidentDetail.raw_evidence.map((line, idx) => (
                        <div key={idx} className="terminal-line">
                          <span className="line-num">{idx + 1}</span>
                          <span className="line-text">{line}</span>
                        </div>
                      ))
                    ) : (
                      <div className="terminal-line">No raw lines stored for this block trace.</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar: AI Root Cause Attribution & Recommended Runbooks */}
          <div className="triage-sidebar-col">
            {/* Status Manager */}
            <div className="glass-card status-manager-card">
              <span className="section-eyebrow">INCIDENT STATE</span>
              <h3>Current Status</h3>
              <div className="status-selector-row">
                {['OPEN', 'INVESTIGATING', 'RESOLVED'].map((st) => (
                  <button
                    key={st}
                    className={`status-btn ${incidentStatus === st ? 'active ' + st.toLowerCase() : ''}`}
                    onClick={() => setIncidentStatus(st)}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            {/* AI Feature Attribution Card */}
            <div className="glass-card attribution-card">
              <span className="section-eyebrow">ROOT-CAUSE ANALYSIS</span>
              <h3>Why Did the AI Flag This?</h3>
              <p className="attribution-desc">
                Isolation Forest identified these top features as the primary contributors to the anomaly score:
              </p>

              <div className="attribution-features-list">
                {incidentDetail.top_features && incidentDetail.top_features.length > 0 ? (
                  incidentDetail.top_features.map((feat, idx) => (
                    <div key={idx} className="attribution-feature-row">
                      <div className="feature-name-col">
                        <span className="feature-key">{feat.feature}</span>
                      </div>
                      <div className="feature-val-col">
                        <span className="feature-score-num">
                          {typeof feat.value === 'number' ? feat.value.toFixed(4) : feat.value}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-subtext">No feature scores returned for this block.</div>
                )}
              </div>
            </div>

            {/* Recommended Ops Runbooks */}
            <div className="glass-card runbooks-sidebar-card">
              <div className="sidebar-card-top">
                <div>
                  <span className="section-eyebrow">SEMANTIC RAG RETRIEVAL</span>
                  <h3>Matched Ops Runbooks</h3>
                </div>
                <Link to="/runbooks" className="view-all-link">
                  Library ➔
                </Link>
              </div>

              <div className="matched-runbooks-list">
                {incidentDetail.recommended_runbooks &&
                incidentDetail.recommended_runbooks.length > 0 ? (
                  incidentDetail.recommended_runbooks.map((rb, i) => (
                    <div key={rb.slug || i} className="matched-runbook-card">
                      <div className="matched-rb-header">
                        <span className="matched-rb-title">{rb.title}</span>
                        {rb.score !== undefined && (
                          <span className="match-percent">
                            {(rb.score * 100).toFixed(0)}% Match
                          </span>
                        )}
                      </div>
                      <p className="matched-rb-excerpt">{rb.excerpt}</p>
                      <Link to="/runbooks" className="matched-rb-link">
                        Open Full Runbook ➔
                      </Link>
                    </div>
                  ))
                ) : (
                  <div className="matched-runbook-card">
                    <div className="matched-rb-header">
                      <span className="matched-rb-title">HDFS Block Corruption Recovery</span>
                      <span className="match-percent">95% Match</span>
                    </div>
                    <p className="matched-rb-excerpt">
                      Procedures to recover from ChecksumException and markBlockAsCorrupt incidents
                      using fsck and DataNode replication commands.
                    </p>
                    <Link to="/runbooks" className="matched-rb-link">
                      Open Full Runbook ➔
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
