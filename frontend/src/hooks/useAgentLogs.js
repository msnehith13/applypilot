import { useState, useEffect, useRef } from 'react'
import { createLogSocket } from '../api'

const MAX_LOGS = 200

export function useAgentLogs() {
  const [logs, setLogs] = useState([])
  const [activeRunId, setActiveRunId] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    function connect() {
      const ws = createLogSocket((msg) => {
        if (msg.type === 'ping') return

        if (msg.type === 'log') {
          setLogs(prev => {
            const next = [...prev, msg]
            return next.length > MAX_LOGS ? next.slice(-MAX_LOGS) : next
          })
          if (msg.run_id) setActiveRunId(msg.run_id)
          setIsRunning(true)
        }

        if (msg.type === 'run_complete' || msg.type === 'run_stopped') {
          setIsRunning(false)
        }
      })

      ws.onclose = () => {
        // Reconnect after 3s if disconnected
        setTimeout(connect, 3000)
      }

      wsRef.current = ws
    }

    connect()
    return () => wsRef.current?.close()
  }, [])

  function clearLogs() { setLogs([]) }

  return { logs, activeRunId, isRunning, clearLogs }
}