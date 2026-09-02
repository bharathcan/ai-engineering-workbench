import { useEffect, useState } from 'react'
import './AppShell.css'
import { listRequirements, type RequirementResponse } from '../api/requirements'
import { useProjectData } from '../hooks/useProjectData'
import { AIRunsScreen } from '../screens/AIRunsScreen'
import { ArtifactsScreen } from '../screens/ArtifactsScreen'
import { DashboardScreen } from '../screens/DashboardScreen'
import { EngineeringPlanScreen } from '../screens/EngineeringPlanScreen'
import { FinalReportScreen } from '../screens/FinalReportScreen'
import { RequirementScreen } from '../screens/RequirementScreen'
import { ScenariosScreen } from '../screens/ScenariosScreen'
import { TasksScreen } from '../screens/TasksScreen'
import { ValidationScreen } from '../screens/ValidationScreen'

export type ScreenId =
  | 'dashboard'
  | 'requirement'
  | 'plan'
  | 'tasks'
  | 'ai-runs'
  | 'artifacts'
  | 'validation'
  | 'scenarios'
  | 'report'

const NAV_ITEMS: { id: ScreenId; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'requirement', label: 'Requirement' },
  { id: 'plan', label: 'Engineering Plan' },
  { id: 'tasks', label: 'Tasks' },
  { id: 'ai-runs', label: 'AI Runs' },
  { id: 'artifacts', label: 'Artifacts' },
  { id: 'validation', label: 'Validation' },
  { id: 'scenarios', label: 'Scenarios' },
  { id: 'report', label: 'Final Report' },
]

export function AppShell() {
  const [activeScreen, setActiveScreen] = useState<ScreenId>('dashboard')
  const [projects, setProjects] = useState<RequirementResponse[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [projectsError, setProjectsError] = useState<string | null>(null)

  const { data, loading, error, reload } = useProjectData(selectedId)

  const refreshProjectList = async () => {
    try {
      const list = await listRequirements()
      setProjects(list)
      setProjectsError(null)
    } catch {
      setProjectsError('Could not load the project list.')
    }
  }

  useEffect(() => {
    refreshProjectList()
  }, [])

  const handleProjectCreated = async (requirementId: string) => {
    await refreshProjectList()
    setSelectedId(requirementId)
    setActiveScreen('requirement')
  }

  const navigateTo = (screen: ScreenId) => setActiveScreen(screen)

  return (
    <div className="app-shell">
      {selectedId && (
        <>
          <header className="app-shell__header">
            <div className="app-shell__brand">AI Engineering Workbench</div>
            <label className="app-shell__project-selector">
              Project:
              <select
                value={selectedId ?? ''}
                onChange={(e) => setSelectedId(e.target.value || null)}
              >
                <option value="">— Select a project —</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.id} — {p.text.slice(0, 60)}
                    {p.text.length > 60 ? '…' : ''}
                  </option>
                ))}
              </select>
            </label>
            {projectsError && <span className="app-shell__error">{projectsError}</span>}
          </header>

          <nav className="app-shell__nav" aria-label="Workbench navigation">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={
                  'app-shell__nav-item' +
                  (activeScreen === item.id ? ' app-shell__nav-item--active' : '')
                }
                onClick={() => navigateTo(item.id)}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </>
      )}

      <main className="app-shell__content">
        {loading && <p className="app-shell__loading">Loading project…</p>}
        {error && <p className="app-shell__error">{error}</p>}

        {activeScreen === 'dashboard' && (
          <DashboardScreen project={data} onNavigate={navigateTo} />
        )}
        {activeScreen === 'requirement' && (
          <RequirementScreen
            project={data}
            onRequirementCreated={handleProjectCreated}
            onAnalyzed={reload}
            onNavigate={navigateTo}
          />
        )}
        {activeScreen === 'plan' && (
          <EngineeringPlanScreen project={data} onPlanGenerated={reload} />
        )}
        {activeScreen === 'tasks' && <TasksScreen project={data} onChanged={reload} />}
        {activeScreen === 'ai-runs' && <AIRunsScreen project={data} />}
        {activeScreen === 'artifacts' && <ArtifactsScreen project={data} onChanged={reload} />}
        {activeScreen === 'validation' && <ValidationScreen project={data} onChanged={reload} />}
        {activeScreen === 'scenarios' && (
          <ScenariosScreen
            project={data}
            onRequirementCreated={handleProjectCreated}
            onNavigate={navigateTo}
          />
        )}
        {activeScreen === 'report' && <FinalReportScreen project={data} />}
      </main>
    </div>
  )
}
