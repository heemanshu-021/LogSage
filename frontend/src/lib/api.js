const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])

function cookieValue(name) {
  const entry = document.cookie.split('; ').find((cookie) => cookie.startsWith(`${name}=`))
  return entry ? decodeURIComponent(entry.slice(name.length + 1)) : ''
}

export function apiFetch(input, init = {}) {
  const method = (init.method || 'GET').toUpperCase()
  const headers = new Headers(init.headers || {})
  if (!SAFE_METHODS.has(method)) {
    const csrf = cookieValue('logsage_csrf')
    if (csrf) headers.set('X-CSRF-Token', csrf)
  }
  return fetch(input, { ...init, headers, credentials: init.credentials || 'include' })
}
