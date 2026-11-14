import { useState, useRef } from 'react'

export default function LogUpload({ apiUrl, onComplete, onError }) {
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
    try {
      let res
      if (mode === 'file' && file) {
        const fd = new FormData()
        fd.append('file', file)
        res = await fetch(`${apiUrl}/logs/ingest/file`, { method: 'POST', body: fd })
      } else {
        const lines = rawText.split('\n').filter(l => l.trim())
        res = await fetch(`${apiUrl}/logs/ingest`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lines, source: 'api' }),
        })
      }
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      onComplete(await res.json())
    } catch (e) {
      onError(e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="card">
      <h2>📤 Ingest Logs</h2>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button className={`btn btn-sm ${mode==='file' ? 'btn-primary' : ''}`} onClick={() => setMode('file')}>File Upload</button>
        <button className={`btn btn-sm ${mode==='text' ? 'btn-primary' : ''}`} onClick={() => setMode('text')}>Paste Text</button>
      </div>

      {mode === 'file' ? (
        <div
          className={`upload-area${drag ? ' drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
        >
          <div className="upload-icon">📁</div>
          {file
            ? <p style={{ color: 'var(--accent-light)' }}>{file.name} ({(file.size/1024).toFixed(1)} KB)</p>
            : <p>Drop a .log / .txt file here or click to browse</p>
          }
          <input ref={inputRef} type="file" accept=".log,.txt,.csv" style={{ display:'none' }}
            onChange={e => { if(e.target.files[0]) setFile(e.target.files[0]) }} />
        </div>
      ) : (
        <textarea
          style={{
            width: '100%', height: '120px', background: 'var(--bg)',
            border: '1px solid var(--border)', borderRadius: 'var(--radius)',
            color: 'var(--text)', padding: '0.75rem', fontFamily: 'monospace',
            fontSize: '0.8rem', resize: 'vertical',
          }}
          placeholder="Paste log lines here…"
          value={rawText}
          onChange={e => setRawText(e.target.value)}
        />
      )}

      <button
        className="btn btn-primary"
        style={{ marginTop: '0.75rem' }}
        disabled={uploading || (mode==='file' ? !file : !rawText.trim())}
        onClick={handleSubmit}
      >
        {uploading ? '⏳ Processing…' : '🚀 Ingest & Detect'}
      </button>
    </div>
  )
}
