import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'

export default function ScanPage({ apiUrl, onAnalysisSuccess }) {
  const [file, setFile] = useState(null)
  const [rawText, setRawText] = useState('')
  const [mode, setMode] = useState('file') // 'file' | 'text'
  const [scanning, setScanning] = useState(false)
  const [drag, setDrag] = useState(false)
  const [scanStep, setScanStep] = useState(0) // 0: Idle, 1: Parse, 2: Featurize, 3: ML Score, 4: Complete
  const [scanResult, setScanResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const inputRef = useRef()
  const navigate = useNavigate()

  const handleDrop = (e) => {
    e.preventDefault()
    setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f) {
      setFile(f)
      setMode('file')
      setErrorMsg('')
    }
  }

  const handleAnalyze = async () => {
    setScanning(true)
    setErrorMsg('')
    setScanResult(null)
    setScanStep(1)

    try {
      let analyzeData

      if (mode === 'file' && file) {
        // Step 1: Upload
        setScanStep(1)
        const fd = new FormData()
        fd.append('file', file)
        const uploadRes = await apiFetch(`${apiUrl}/api/logs/upload`, {
          method: 'POST',
          body: fd,
        })
        if (!uploadRes.ok) {
          const err = await uploadRes.json().catch(() => ({}))
          throw new Error(err.detail || `Upload failed (HTTP ${uploadRes.status})`)
        }
        const uploadData = await uploadRes.json()

        // Step 2 & 3: Run pipeline
        setScanStep(2)
        await new Promise((r) => setTimeout(r, 400))
        setScanStep(3)

        const analyzeRes = await apiFetch(`${apiUrl}/api/logs/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: uploadData.file_id }),
        })
        if (!analyzeRes.ok) {
          const err = await analyzeRes.json().catch(() => ({}))
          throw new Error(err.detail || `Analysis failed (HTTP ${analyzeRes.status})`)
        }
        analyzeData = await analyzeRes.json()
      } else {
        // Text mode
        const lines = rawText.split('\n').filter((l) => l.trim())
        if (!lines.length) {
          throw new Error('Please enter or paste at least one log line.')
        }

        setScanStep(2)
        await new Promise((r) => setTimeout(r, 300))
        setScanStep(3)

        const res = await apiFetch(`${apiUrl}/api/logs/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lines }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || `Server error (HTTP ${res.status})`)
        }
        analyzeData = await res.json()
      }

      setScanStep(4)
      setScanResult(analyzeData)
      if (onAnalysisSuccess) onAnalysisSuccess(analyzeData)
    } catch (err) {
      setErrorMsg(err.message || 'Log analysis failed')
      setScanStep(0)
    } finally {
      setScanning(false)
    }
  }

  const loadPreset = (presetType) => {
    setMode('text')
    setErrorMsg('')
    setScanResult(null)

    if (presetType === 'corrupt') {
      setRawText(
`081109 203615 148 INFO dfs.DataNode: Receiving block blk_999 from /10.251.215.16
081109 203616 148 ERROR dfs.DataNode: IOException in DataXceiver for block blk_999
081109 203617 35  ERROR dfs.FSNamesystem: BLOCK NameSystem.markBlockAsCorrupt: blk_999
081109 203618 148 WARN dfs.DataNode: Failed to replicate block blk_999 to node 10.251.215.18
081109 203619 148 INFO dfs.DataNode: Receiving block blk_100 from /10.251.215.19
081109 203620 148 INFO dfs.DataNode: Received block blk_100 of size 67108864 from /10.251.215.19`
      )
    } else if (presetType === 'normal') {
      setRawText(
`081109 203615 148 INFO dfs.DataNode: Receiving block blk_501 from /10.251.215.16
081109 203616 148 INFO dfs.DataNode: Received block blk_501 of size 67108864 from /10.251.215.16
081109 203617 148 INFO dfs.DataNode: PacketResponder 1 for block blk_501 terminating
081109 203618 148 INFO dfs.DataNode: Receiving block blk_502 from /10.251.215.17
081109 203619 148 INFO dfs.DataNode: Received block blk_502 of size 67108864 from /10.251.215.17
081109 203620 148 INFO dfs.DataNode: PacketResponder 2 for block blk_502 terminating`
      )
    } else {
      setRawText(
`081109 203621 148 WARN dfs.DataNode: Slow I/O in DataXceiver for block blk_777: write took 4500ms
081109 203622 148 WARN dfs.DataNode: DataNode disk write latency exceeds 3000ms threshold on /data1
081109 203623 148 INFO dfs.DataNode: PacketResponder for block blk_777 completed with retry count 3`
      )
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <span className="page-tag">DATA INGESTION & PIPELINE</span>
          <h1 className="page-title">Ingest & Scan Logs</h1>
          <p className="page-desc">
            Upload raw log dumps or paste text traces to execute Drain3 pattern extraction,
            feature aggregation, and Isolation Forest anomaly inference.
          </p>
        </div>
      </div>

      <div className="scan-layout">
        {/* Main Upload Box */}
        <div className="glass-card scan-card">
          <div className="scan-controls-top">
            <div className="mode-tabs">
              <button
                className={`tab-btn ${mode === 'file' ? 'active' : ''}`}
                onClick={() => setMode('file')}
              >
                📁 File Upload
              </button>
              <button
                className={`tab-btn ${mode === 'text' ? 'active' : ''}`}
                onClick={() => setMode('text')}
              >
                📝 Paste Raw Logs
              </button>
            </div>

            <div className="preset-buttons">
              <span className="preset-label">Sample Presets:</span>
              <button
                type="button"
                className="btn-preset text-danger"
                onClick={() => loadPreset('corrupt')}
              >
                HDFS Corruption
              </button>
              <button
                type="button"
                className="btn-preset text-ok"
                onClick={() => loadPreset('normal')}
              >
                Normal Flow
              </button>
              <button
                type="button"
                className="btn-preset text-warn"
                onClick={() => loadPreset('warn')}
              >
                Disk Latency
              </button>
            </div>
          </div>

          {mode === 'file' ? (
            <div
              className={`dropzone-area ${drag ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
              onDragLeave={() => setDrag(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current && inputRef.current.click()}
            >
              <div className="dropzone-icon">📥</div>
              {file ? (
                <div className="file-preview-info">
                  <div className="file-name">{file.name}</div>
                  <div className="file-meta">
                    {(file.size / 1024).toFixed(1)} KB · Ready to scan
                  </div>
                  <span className="file-switch-hint">Click or drag a new file to replace</span>
                </div>
              ) : (
                <div className="dropzone-text">
                  <h3>Drop your log file here, or browse</h3>
                  <p>Supports .log, .txt, and .csv files up to 25 MB</p>
                </div>
              )}
              <input
                ref={inputRef}
                type="file"
                accept=".log,.txt,.csv"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setFile(e.target.files[0])
                    setErrorMsg('')
                  }
                }}
              />
            </div>
          ) : (
            <div className="textarea-wrapper">
              <textarea
                className="code-textarea"
                rows={10}
                placeholder="Paste log stream here (e.g. HDFS DataNode lines)..."
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
              />
            </div>
          )}

          {errorMsg && (
            <div className="error-banner">
              <span className="error-icon">⚠️</span>
              <span>{errorMsg}</span>
            </div>
          )}

          <div className="scan-actions">
            <button
              className="btn btn-primary btn-lg"
              disabled={scanning || (mode === 'file' ? !file : !rawText.trim())}
              onClick={handleAnalyze}
            >
              {scanning ? (
                <span className="btn-spinner-content">
                  <span className="spinner" /> Running AI Pipeline...
                </span>
              ) : (
                <span>🚀 Execute Anomaly Pipeline</span>
              )}
            </button>

            {mode === 'file' && file && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  setFile(null)
                  if (inputRef.current) inputRef.current.value = ''
                }}
              >
                Clear File
              </button>
            )}
          </div>
        </div>

        {/* Live Pipeline Steps Visualizer */}
        {scanning && (
          <div className="glass-card pipeline-visualizer">
            <h3>Pipeline Execution in Progress</h3>
            <div className="pipeline-steps">
              <div className={`step-item ${scanStep >= 1 ? 'active' : ''}`}>
                <div className="step-circle">{scanStep > 1 ? '✓' : '1'}</div>
                <div className="step-content">
                  <div className="step-name">Drain3 Log Parsing</div>
                  <div className="step-desc">Tokenizing parameters & template extraction</div>
                </div>
              </div>
              <div className={`step-item ${scanStep >= 2 ? 'active' : ''}`}>
                <div className="step-circle">{scanStep > 2 ? '✓' : '2'}</div>
                <div className="step-content">
                  <div className="step-name">Block Aggregation & Features</div>
                  <div className="step-desc">Extracting entropy, rare events & error ratios</div>
                </div>
              </div>
              <div className={`step-item ${scanStep >= 3 ? 'active' : ''}`}>
                <div className="step-circle">{scanStep > 3 ? '✓' : '3'}</div>
                <div className="step-content">
                  <div className="step-name">Isolation Forest Scoring</div>
                  <div className="step-desc">Predicting outlier decision boundary</div>
                </div>
              </div>
              <div className={`step-item ${scanStep >= 4 ? 'active' : ''}`}>
                <div className="step-circle">{scanStep >= 4 ? '✓' : '4'}</div>
                <div className="step-content">
                  <div className="step-name">Incident Staging & Runbook RAG</div>
                  <div className="step-desc">Matching operational resolution runbooks</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Scan Results Card */}
        {scanResult && !scanning && (
          <div className="glass-card result-card">
            <div className="result-header">
              <div className="result-title-group">
                <span className="badge badge-resolved">SCAN COMPLETED</span>
                <h2>Analysis Completed in {scanResult.processing_time_ms.toFixed(1)} ms</h2>
              </div>
              <button
                className="btn btn-primary"
                onClick={() => navigate('/incidents')}
              >
                View Incidents Table ➔
              </button>
            </div>

            <div className="result-stats-row">
              <div className="result-stat-box">
                <span className="stat-label">LOGS PARSED</span>
                <span className="stat-num">{scanResult.total_lines.toLocaleString()}</span>
              </div>
              <div className="result-stat-box">
                <span className="stat-label">BLOCKS IDENTIFIED</span>
                <span className="stat-num">{scanResult.total_blocks}</span>
              </div>
              <div className="result-stat-box">
                <span className="stat-label">ANOMALIES FLAGGED</span>
                <span className="stat-num text-danger">{scanResult.anomalous_blocks}</span>
              </div>
              <div className="result-stat-box">
                <span className="stat-label">INCIDENTS CREATED</span>
                <span className="stat-num text-accent">{scanResult.incidents_created}</span>
              </div>
            </div>

            {scanResult.incidents && scanResult.incidents.length > 0 && (
              <div className="flagged-preview-box">
                <h4>Flagged Anomalies Detected:</h4>
                <div className="flagged-cards-mini">
                  {scanResult.incidents.map((inc) => (
                    <div key={inc.incident_id} className="mini-inc-card">
                      <span className={`badge badge-${(inc.severity || 'LOW').toLowerCase()}`}>
                        {inc.severity}
                      </span>
                      <span className="mini-inc-id">{inc.incident_id}</span>
                      <span className="mini-inc-block">{inc.block_id}</span>
                      <span className="mini-inc-score">Score: {inc.anomaly_score.toFixed(3)}</span>
                      <button
                        className="btn btn-glass btn-sm"
                        onClick={() => navigate('/triage')}
                      >
                        Solve ➔
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
