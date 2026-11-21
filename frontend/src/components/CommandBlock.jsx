import { useState } from 'react'

export default function CommandBlock({ command, description }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(command)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback if clipboard API is restricted
      const el = document.createElement('textarea')
      el.value = command
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="command-block-container">
      {description && <div className="command-desc">{description}</div>}
      <div className="command-box">
        <div className="command-text">
          <span className="command-prompt">$</span>
          <code>{command}</code>
        </div>
        <button
          type="button"
          className={`copy-btn ${copied ? 'copied' : ''}`}
          onClick={handleCopy}
          title="Copy command to clipboard"
        >
          {copied ? (
            <>
              <span className="copy-icon">✓</span>
              <span>Copied!</span>
            </>
          ) : (
            <>
              <span className="copy-icon">📋</span>
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
