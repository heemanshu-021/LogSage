import { useState, useRef } from 'react'
import { apiFetch } from '../lib/api'

export default function LogUpload({ apiUrl, onComplete, onError, onStart }) {
  const [file, setFile] = useState(null)
  const [rawText, setRawText] = useState('')
  const [mode, setMode] = useState('file')   // 'file' | 'text'
  const [uploading, setUploading] = useState(false)
  const [drag, setDrag] = useState(false)
  const inputRef = useRef()

  const handleDrop = (e) => {
    e.preventDefault()
    setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f) { setFile(f); setMode('file') }
  }

  const handleSubmit = async () => {
    setUploading(true)
    if (onStart) onStart()
    try {
      let analyzeData

      if (mode === 'file' && file) {
        // Step 1: Upload file to /api/logs/upload
        const fd = new FormData()
        fd.append('file', file)
        const uploadRes = await apiFetch(`${apiUrl}/api/logs/upload`, {
          method: 'POST',
          body: fd,
        })
        if (!uploadRes.ok) {
          const errBody = await uploadRes.json().catch(() => ({}))
          throw new Error(errBody.detail || `Upload failed: HTTP ${uploadRes.status}`)
        }
        const uploadData = await uploadRes.json()

        // Step 2: Trigger analysis on staged file using file_id as session_id
        const analyzeRes = await apiFetch(`${apiUrl}/api/logs/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: uploadData.file_id }),
        })
        if (!analyzeRes.ok) {
          const errBody = await analyzeRes.json().catch(() => ({}))
          throw new Error(errBody.detail || `Analysis failed: HTTP ${analyzeRes.status}`)
        }
        analyzeData = await analyzeRes.json()
      } else {
        // Direct inline analysis on log lines
        const lines = rawText.split('\n').filter(l => l.trim())
        if (!lines.length) {
          throw new Error('Please enter at least one log line.')
        }
        const res = await apiFetch(`${apiUrl}/api/logs/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lines }),
        })
        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}))
          throw new Error(errBody.detail || `Server error: HTTP ${res.status}`)
        }
        analyzeData = await res.json()
      }

      onComplete(analyzeData)
    } catch (e) {
      onError(e.message || 'Log analysis failed')
    } finally {
      setUploading(false)
    }
  }

  const loadSampleData = () => {
    setMode('text')
    setRawText(
`081109 203615 148 INFO dfs.DataNode: Receiving block blk_100 from /10.0.0.1
081109 203616 148 INFO dfs.DataNode: Receiving block blk_101 from /10.0.0.2
081109 203617 148 ERROR dfs.DataNode: IOException in DataXceiver for block blk_999
081109 203618 35 ERROR dfs.FSNamesystem: BLOCK NameSystem markBlockAsCorrupt blk_999
081109 203619 148 INFO dfs.DataNode: Receiving block blk_102 from /10.0.0.3
081109 203620 148 INFO dfs.DataNode: Receiving block blk_103 from /10.0.0.4
081109 203623 35 WARN dfs.DataNode: Slow I/O for block blk_200`
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>📤 Ingest & Analyze Logs</h2>
        <button
          className="btn btn-secondary btn-sm"
          onClick={loadSampleData}
          title="Paste sample anomalous HDFS log records"
        >
          Load Sample
        </button>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button
          className={`btn btn-sm ${mode === 'file' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setMode('file')}
        >
          File Upload (.log, .txt, .csv)
        </button>
        <button
          className={`btn btn-sm ${mode === 'text' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setMode('text')}
        >
          Raw Log Text
        </button>
      </div>

      {mode === 'file' ? (
        <div
          className={`upload-area${drag ? ' drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current && inputRef.current.click()}
        >
          <div className="upload-icon">📁</div>
          {file ? (
            <div>
              <p style={{ color: 'var(--accent-light)', fontWeight: 600 }}>{file.name}</p>
              <p style={{ fontSize: '0.75rem' }}>{(file.size / 1024).toFixed(1)} KB · Ready to analyze</p>
            </div>
          ) : (
            <div>
              <p style={{ fontWeight: 500, color: '#fff' }}>Click to browse or drag & drop log files</p>
              <p>Supports HDFS, syslog, text dumps up to 25 MB</p>
            </div>
          )}
          <input
            ref={inputRef}
            type="file"
            accept=".log,.txt,.csv"
            style={{ display: 'none' }}
            onChange={e => { if (e.target.files && e.target.files[0]) setFile(e.target.files[0]) }}
          />
        </div>
      ) : (
        <textarea
          style={{
            width: '100%',
            height: '140px',
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            color: 'var(--text)',
            padding: '0.75rem',
            fontFamily: 'Consolas, Monaco, monospace',
            fontSize: '0.78rem',
            resize: 'vertical',
            outline: 'none',
          }}
          placeholder="Paste raw log lines here (one per line)..."
          value={rawText}
          onChange={e => setRawText(e.target.value)}
        />
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
        <button
          className="btn btn-primary"
          disabled={uploading || (mode === 'file' ? !file : !rawText.trim())}
          onClick={handleSubmit}
        >
          {uploading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="spinner" /> Parsing & Scoring...
            </span>
          ) : (
            '🚀 Run Anomaly Pipeline'
          )}
        </button>
        {mode === 'file' && file && (
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => { setFile(null); if (inputRef.current) inputRef.current.value = '' }}
          >
            Clear File
          </button>
        )}
      </div>
    </div>
  )
}
