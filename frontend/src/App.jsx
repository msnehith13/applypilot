import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/SideBar'
import Dashboard from './pages/Dashboard'
import Applications from './pages/Applications'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import { useAgentLogs } from './hooks/useAgentLogs'

export default function App() {
  const { logs, isRunning, activeRunId, clearLogs } = useAgentLogs()

  return (
    <div className="flex min-h-screen bg-bg-base">
      <Sidebar isRunning={isRunning} />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/"             element={<Dashboard logs={logs} isRunning={isRunning} activeRunId={activeRunId} clearLogs={clearLogs} />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/profile"      element={<Profile />} />
          <Route path="/settings"     element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}