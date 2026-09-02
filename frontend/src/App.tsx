import { useEffect, useState } from 'react'
import './App.css'
import { fetchHealth } from './api/health'
import { AppShell } from './components/AppShell'

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
    <>
      <p className={`status status--${backend.state} status--bar`}>
        {backend.state === 'loading' && 'Status: Checking backend…'}
        {backend.state === 'connected' && 'Status: Connected'}
        {backend.state === 'unavailable' && 'Status: Backend unavailable'}
      </p>
      <AppShell />
    </>
  )
}

export default App
