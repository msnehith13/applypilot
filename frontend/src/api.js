const BASE = '/api'

async function req(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body) opts.body = JSON.stringify(body)
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  // Profile
  getProfile:    ()       => req('GET',  '/profile'),
  updateProfile: (data)   => req('PUT',  '/profile', data),
  uploadResume:  (file)   => {
    const fd = new FormData()
    fd.append('file', file)
    return fetch(BASE + '/profile/resume', { method: 'POST', body: fd }).then(r => r.json())
  },

  // Runs
  startRun:  (portals, max) => req('POST', '/runs', { portals, max_applications: max }),
  listRuns:  ()             => req('GET',  '/runs'),
  getRun:    (id)           => req('GET',  `/runs/${id}`),
  stopRun:   (id)           => req('POST', `/runs/${id}/stop`),
  getRunLogs:(id)           => req('GET',  `/runs/${id}/logs`),

  // Applications
  listApps: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return req('GET', `/applications${qs ? '?' + qs : ''}`)
  },
  getApp: (id) => req('GET', `/applications/${id}`),

  // Stats
  getStats: () => req('GET', '/stats'),
}

// WebSocket helper
export function createLogSocket(onMessage) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${proto}://${location.host}/ws/logs`)
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)) } catch {}
  }
  ws.onerror = () => console.warn('WS error — will retry')
  return ws
}