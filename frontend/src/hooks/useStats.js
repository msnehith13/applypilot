import { useState, useEffect } from 'react'
import { api } from '../api'

export function useStats() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const data = await api.getStats()
        if (!cancelled) { setStats(data); setLoading(false) }
      } catch (e) {
        console.error('stats fetch failed', e)
        if (!cancelled) setLoading(false)
      }
    }

    load()
    const id = setInterval(load, 10_000)
    return () => { cancelled = true; clearInterval(id) }
  }, [])

  return { stats, loading }
}