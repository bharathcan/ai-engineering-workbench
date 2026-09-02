import type { ScreenId } from '../components/AppShell'
import type { RequirementResponse } from '../api/requirements'
import { flattenAiRuns, flattenArtifacts, flattenValidations, type ProjectData } from '../hooks/useProjectData'
import { computeWorkflowStage } from '../hooks/workflowStage'
import { ProjectNetwork } from '../components/ProjectNetwork'
import { FlowSteps } from '../components/FlowSteps'
import { StageFlow } from './StageFlow'
import { TalpLanding } from './TalpLanding'

export function DashboardScreen({
  project,
  onNavigate,
  projects,
  projectsError,
  selectedProjectId,
  onProjectSelect,
}: {
  project: ProjectData | null
  onNavigate: (screen: ScreenId) => void
  projects?: RequirementResponse[]
  projectsError?: string | null
  selectedProjectId?: string | null
  onProjectSelect?: (projectId: string) => void
}) {
  if (!project) {
    return (
      <TalpLanding
        onNavigate={onNavigate}
        projects={projects}
        projectsError={projectsError}
        selectedProjectId={selectedProjectId}
        onProjectSelect={onProjectSelect}
      />
    )
  }

  return <DashboardProject project={project} />
}


function DashboardProject({ project }: { project: ProjectData }) {
  const { requirement, plan, artifactsByTaskId, validationsByArtifactId } = project
  const stage = computeWorkflowStage(project)

  const totalTasks = plan?.tasks.length ?? 0
  const approvedTasks = plan?.tasks.filter((t) => t.status === 'APPROVED').length ?? 0
  const aiRunCount = flattenAiRuns(plan).length
  const artifactCount = flattenArtifacts(plan, artifactsByTaskId).length
  const validations = flattenValidations(plan, artifactsByTaskId, validationsByArtifactId)
  const passed = validations.filter((v) => v.validation.status === 'PASSED').length
  const failed = validations.filter((v) => v.validation.status === 'FAILED').length

  return (
    <div className="project-dashboard-container">
      <div className="project-dashboard">
      {/* Header */}
      <div className="project-header">
        <div className="project-header__content">
          <h1 className="project-header__id">{requirement.id}</h1>
          <p className="project-header__text">{requirement.text}</p>
        </div>
      </div>

      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-bar__stage">
          <span className="status-bar__label">Current Stage</span>
          <span className="status-bar__value">{stage.label}</span>
        </div>
        <div className="status-bar__flow">
          <StageFlow currentIndex={stage.index} />
        </div>
      </div>

      {/* Alerts */}
      {plan?.status === 'BLOCKED' && (
        <div className="alert alert--error">
          <span className="alert__icon">⚠️</span>
          <div>
            <div className="alert__title">Plan Blocked</div>
            <div className="alert__message">{plan.blocked_reason}</div>
          </div>
        </div>
      )}

      {/* Project Network Visualization */}
      <ProjectNetwork tasks={plan?.tasks} />

      {/* Metrics Grid */}
      <div className="metrics-section">
        <h2 className="metrics-section__title">Project Overview</h2>
        <div className="metrics-grid">
          <MetricCard
            label="Tasks"
            value={`${approvedTasks}/${totalTasks}`}
            status={approvedTasks === totalTasks ? 'complete' : 'progress'}
            icon="✓"
          />
          <MetricCard
            label="AI Runs"
            value={aiRunCount}
            status={aiRunCount > 0 ? 'active' : 'inactive'}
            icon="⚡"
          />
          <MetricCard
            label="Artifacts"
            value={artifactCount}
            status={artifactCount > 0 ? 'active' : 'inactive'}
            icon="📦"
          />
          <MetricCard
            label="Validations"
            value={`${passed}/${validations.length}`}
            status={failed === 0 && passed > 0 ? 'success' : failed > 0 ? 'warning' : 'neutral'}
            icon={failed === 0 ? '✓' : '⚠'}
          />
        </div>
      </div>

      {/* Quick Tips */}
      <div className="tips-box">
        <div className="tips-box__icon">💡</div>
        <div className="tips-box__content">
          <div className="tips-box__title">Next Step</div>
          <div className="tips-box__text">
            Follow the workflow: Requirement → Plan → Tasks → AI Runs → Artifacts → Validation → Final Report
          </div>
        </div>
      </div>
    </div>

    <aside className="project-sidebar">
      <FlowSteps currentStep={stage.index} />
    </aside>
    </div>
  )
}


function MetricCard({
  label,
  value,
  status,
  icon,
}: {
  label: string
  value: string | number
  status: string
  icon: string
}) {
  return (
    <div className={`metric-card metric-card--${status}`}>
      <div className="metric-card__icon">{icon}</div>
      <div className="metric-card__content">
        <div className="metric-card__value">{value}</div>
        <div className="metric-card__label">{label}</div>
      </div>
    </div>
  )
}
