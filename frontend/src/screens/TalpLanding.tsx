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

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const list = await listRequirements()
        setProjects(list)
      } catch {
        setProjects([])
      }
    }
    fetchProjects()
  }, [])
  return (
    <>
      <NetworkBackground />

      {/* Header */}
      <header className="header">
        <div className="header__logo">⚡ AI Workbench</div>
      </header>

      {/* Projects Selector */}
      <div className="projects-bar">
        <div className="projects-bar__content">
          <span className="projects-bar__label">Projects:</span>
          <select
            className="projects-dropdown"
            value={selectedProjectId || ''}
            onChange={(e) => e.target.value && onProjectSelect?.(e.target.value)}
          >
            <option value="">-- Select a Project --</option>
            {projects.length > 0 ? (
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.id}
                </option>
              ))
            ) : null}
          </select>
        </div>
      </div>

      {/* Main Container */}
      <div className="container">
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
