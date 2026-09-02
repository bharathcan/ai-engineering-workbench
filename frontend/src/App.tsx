import { useEffect, useState } from 'react'
import './App.css'
import { fetchHealth } from './api/health'
import { RequirementAnalyzer } from './components/RequirementAnalyzer'

type BackendStatus =
  | { state: 'loading' }
  | { state: 'connected' }
  | { state: 'unavailable' }

function App() {
  const [backend, setBackend] = useState<BackendStatus>({ state: 'loading' })

  useEffect(() => {
    let cancelled = false

    fetchHealth()
      .then((health) => {
        if (cancelled) return
        setBackend(health.status === 'ok' ? { state: 'connected' } : { state: 'unavailable' })
      })
      .catch(() => {
        if (!cancelled) setBackend({ state: 'unavailable' })
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="shell">
      <h1>AI Engineering Workbench</h1>
      <p>
        Transform software requirements into
        <br />
        validated engineering outcomes with AI assistance.
      </p>
      <p className={`status status--${backend.state}`}>
        {backend.state === 'loading' && 'Status: Checking backend…'}
        {backend.state === 'connected' && 'Status: Connected'}
        {backend.state === 'unavailable' && 'Status: Backend unavailable'}
      </p>

      <RequirementAnalyzer />
    </main>
  )
}

export default App
