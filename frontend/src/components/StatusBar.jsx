export default function StatusBar({ status }) {
  const cls = `status-bar status-${status.type}`
  const icon = { idle: 'ℹ️', success: '✅', error: '❌', loading: '⏳' }[status.type] || 'ℹ️'
  return (
    <div className={cls}>
      {icon} {status.message}
    </div>
  )
}
