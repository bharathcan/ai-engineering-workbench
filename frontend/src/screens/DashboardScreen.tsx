import type { ScreenId } from '../components/AppShell'
import type { RequirementResponse } from '../api/requirements'
import { flattenAiRuns, flattenArtifacts, flattenValidations, type ProjectData } from '../hooks/useProjectData'
import { computeWorkflowStage } from '../hooks/workflowStage'
import { ProjectNetwork } from '../components/ProjectNetwork'
import { FlowSteps } from '../components/FlowSteps'
import { StageFlow } from './StageFlow'
import { TalpLanding } from './TalpLanding'
import './DashboardProject.css'

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
        <div className="proj-header">
          <h1 className="proj-header__id">{requirement.id}</h1>
          <p className="proj-header__text">{requirement.text}</p>
        </div>

        {/* Status Bar */}
        <div className="proj-status">
          <div className="proj-status__row">
            <span className="proj-status__label">Current Stage</span>
            <span className={`proj-status__value${plan?.status === 'BLOCKED' ? ' proj-status__value--blocked' : ''}`}>
              {stage.label}
            </span>
          </div>
          <StageFlow currentIndex={stage.index} />
        </div>

        {/* Alerts */}
        {plan?.status === 'BLOCKED' && (
          <div className="proj-alert">
            <span className="proj-alert__icon">⚠️</span>
            <div>
              <div className="proj-alert__title">Plan Blocked</div>
              <div className="proj-alert__message">{plan.blocked_reason}</div>
            </div>
          </div>
        )}

        {/* Project Network Visualization */}
        <ProjectNetwork tasks={plan?.tasks} />

        {/* Metrics Grid */}
        <div className="proj-metrics">
          <h2 className="proj-metrics__title">Project Overview</h2>
          <div className="proj-metrics__grid">
            <MetricCard
              label="Tasks"
              value={`${approvedTasks}/${totalTasks}`}
              status={approvedTasks === totalTasks && totalTasks > 0 ? 'complete' : 'progress'}
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
        <div className="proj-tip">
          <div className="proj-tip__icon">💡</div>
          <div>
            <div className="proj-tip__title">Next Step</div>
            <div className="proj-tip__text">
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
    <div className={`proj-metric proj-metric--${status}`}>
      <div className="proj-metric__icon">{icon}</div>
      <div>
        <div className="proj-metric__value">{value}</div>
        <div className="proj-metric__label">{label}</div>
      </div>
    </div>
  )
}
