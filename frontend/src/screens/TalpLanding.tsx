import { useEffect, useState } from 'react'
import '../styles/talp-design.css'
import { NetworkBackground } from '../components/NetworkBackground'
import { listRequirements, type RequirementResponse } from '../api/requirements'
import type { ScreenId } from '../components/AppShell'

export function TalpLanding({ onNavigate, selectedProjectId, onProjectSelect }: {
  onNavigate: (screen: ScreenId) => void
  selectedProjectId?: string | null
  onProjectSelect?: (projectId: string) => void
}) {
  const [projects, setProjects] = useState<RequirementResponse[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true)
        setLoadError(null)
        const list = await listRequirements()
        setProjects(list)
      } catch (error) {
        setLoadError('Unable to load projects. Backend service is unavailable.')
        setProjects([])
      } finally {
        setLoading(false)
      }
    }
    fetchProjects()
  }, [])
  return (
    <>
      <NetworkBackground />

      {/* Error Banner */}
      {loadError && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          padding: '1rem 2rem',
          background: '#fef3c7',
          borderBottom: '2px solid #f59e0b',
          color: '#92400e',
          textAlign: 'center',
          fontSize: '0.95rem',
          fontWeight: 600,
        }}>
          ⚠️ {loadError}
        </div>
      )}

      {/* Header */}
      <header className="header">
        <div className="header__logo">⚡ AI Workbench</div>
      </header>

      {/* Projects Selector */}
      <div className="projects-bar">
        <div className="projects-bar__content">
          <span className="projects-bar__label">Projects:</span>
          {loadError && (
            <div style={{
              color: '#92400e',
              fontSize: '0.9rem',
              padding: '0.5rem 1rem',
              background: '#fef3c7',
              borderRadius: '4px',
              marginRight: '1rem',
              border: '1px solid #f59e0b'
            }}>
              ⚠️ {loadError}
            </div>
          )}
          {!loadError && (
            <select
              className="projects-dropdown"
              value={selectedProjectId || ''}
              onChange={(e) => {
                if (e.target.value) {
                  onProjectSelect?.(e.target.value)
                  onNavigate('dashboard')
                }
              }}
              disabled={loading}
            >
              <option value="">
                {loading ? '-- Loading Projects --' : '-- Select a Project --'}
              </option>
              {projects.length > 0 ? (
                projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.id}
                  </option>
                ))
              ) : null}
            </select>
          )}
        </div>
      </div>

      {/* Main Container */}
      <div className="container" style={{ paddingTop: loadError ? '120px' : '80px' }}>
        {/* Hero Section */}
        <section className="hero">
          <div className="hero__content">
            <span className="hero__category">.dashboard</span>
            <h1 className="hero__title">
              AI Engineering <span className="hero__accent">Workbench</span>
            </h1>
            <p className="hero__subtitle">
              Select a project above or create a new one to get started.
            </p>
            <button className="hero__cta" onClick={() => onNavigate('requirement')}>
              New Project
            </button>
          </div>
        </section>

      </div>
    </>
  )
}
