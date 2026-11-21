import { Link, useLocation } from 'react-router-dom'

export default function Navbar({ health, openIncidentsCount }) {
  const location = useLocation()

  const navLinks = [
    { path: '/', label: 'Overview', icon: '⚡' },
    { path: '/scan', label: 'Ingest & Scan', icon: '📥' },
    { path: '/incidents', label: 'Incidents', icon: '🚨', badge: openIncidentsCount > 0 ? openIncidentsCount : null },
    { path: '/triage', label: 'Triage Room', icon: '🛠️' },
    { path: '/runbooks', label: 'Runbooks', icon: '📖' },
  ]

  const isModelReady = health?.ml_model_loaded
  const isApiOnline = health?.status === 'ok'

  return (
    <header className="navbar">
      <div className="navbar-left">
        <Link to="/" className="brand">
          <div className="brand-logo-glow">🛡️</div>
          <div className="brand-text">
            <span className="brand-title">LogSage</span>
            <span className="brand-badge">Autonomous Ops</span>
          </div>
        </Link>
      </div>

      <nav className="navbar-links">
        {navLinks.map((item) => {
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.badge !== undefined && item.badge !== null && (
                <span className="nav-badge-pill">{item.badge}</span>
              )}
            </Link>
          )
        })}
      </nav>

      <div className="navbar-right">
        <div className="system-status-pill">
          <span className={`status-orb ${isApiOnline ? 'online' : 'offline'}`} />
          <span className="status-meta">
            API: <strong>{isApiOnline ? 'Online' : 'Disconnected'}</strong>
            <span className="meta-sep">·</span>
            ML: <strong className={isModelReady ? 'text-accent' : 'text-warn'}>
              {isModelReady ? 'Isolation Forest' : 'Fallback'}
            </strong>
          </span>
        </div>
      </div>
    </header>
  )
}
