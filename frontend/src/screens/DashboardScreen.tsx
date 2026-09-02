import './DashboardScreen.css'
import type { ScreenId } from '../components/AppShell'
import { flattenAiRuns, flattenArtifacts, flattenValidations, type ProjectData } from '../hooks/useProjectData'
import { computeWorkflowStage } from '../hooks/workflowStage'
import { StageFlow } from './StageFlow'

export function DashboardScreen({
  project,
  onNavigate,
}: {
  project: ProjectData | null
  onNavigate: (screen: ScreenId) => void
}) {
  if (!project) {
    return (
      <div className="dashboard-landing">
        <div className="dashboard-landing__hero">
          <div className="dashboard-landing__icon">🚀</div>
          <h1 className="dashboard-landing__title">AI Engineering Workbench</h1>
          <p className="dashboard-landing__subtitle">
            Transform requirements into production-grade engineering outcomes
          </p>
          <div className="dashboard-landing__description">
            <p>Your AI-assisted development platform where:</p>
            <ul className="dashboard-landing__features">
              <li>✨ AI accelerates development within structured tasks</li>
              <li>👨‍💼 You maintain full control and ownership</li>
              <li>✅ Every output is validated and tracked</li>
              <li>📊 Complete visibility into the entire workflow</li>
            </ul>
          </div>
          <button
            type="button"
            className="dashboard-landing__cta"
            onClick={() => onNavigate('requirement')}
          >
            Start New Project
          </button>
          <p className="dashboard-landing__hint">
            Or select an existing project from the dropdown above
          </p>
        </div>

        <div className="dashboard-landing__workflow">
          <h2>How It Works</h2>
          <div className="workflow-steps">
            <WorkflowStep
              number={1}
              icon="📝"
              title="Create Requirement"
              description="Describe what you want to build, enhance, or optimize"
            />
            <WorkflowStep
              number={2}
              icon="🤖"
              title="AI Analysis"
              description="AI analyzes requirements and identifies scope, ambiguities, constraints"
            />
            <WorkflowStep
              number={3}
              icon="📋"
              title="Task Breakdown"
              description="AI decomposes into structured engineering tasks with dependencies"
            />
            <WorkflowStep
              number={4}
              icon="💡"
              title="AI Recommendations"
              description="Get AI assistance for each task with approach and implementation suggestions"
            />
            <WorkflowStep
              number={5}
              icon="📦"
              title="Generate Artifacts"
              description="AI generates actual code, tests, APIs, and documentation"
            />
            <WorkflowStep
              number={6}
              icon="✔️"
              title="Validate & Review"
              description="Multi-stage validation ensures quality before approval"
            />
          </div>
        </div>
      </div>
    )
  }

  const { requirement, plan, artifactsByTaskId, validationsByArtifactId } = project
  const stage = computeWorkflowStage(project)

  const totalTasks = plan?.tasks.length ?? 0
  const approvedTasks = plan?.tasks.filter((t) => t.status === 'APPROVED').length ?? 0
  const aiRunCount = flattenAiRuns(plan).length
  const artifactCount = flattenArtifacts(plan, artifactsByTaskId).length
  const validations = flattenValidations(plan, artifactsByTaskId, validationsByArtifactId)
  const passed = validations.filter((v) => v.validation.status === 'PASSED').length
  const failed = validations.filter((v) => v.validation.status === 'FAILED').length
  const notValidated = validations.filter((v) => v.validation.status === 'NOT_VALIDATED').length

  return (
    <div className="dashboard-project">
      <div className="dashboard-project__header">
        <h2>{requirement.id}</h2>
        <p className="dashboard-project__requirement">{requirement.text}</p>
      </div>

      <div className="dashboard-project__stage">
        <div className="stage-info">
          <h3>Current Stage</h3>
          <p className="stage-label">{stage.label}</p>
        </div>
        <StageFlow currentIndex={stage.index} />
      </div>

      {plan?.status === 'BLOCKED' && (
        <div className="alert alert--blocked">
          <span className="alert__icon">⚠️</span>
          <span>Blocked: {plan.blocked_reason}</span>
        </div>
      )}

      <div className="dashboard-project__metrics">
        <h3>Project Metrics</h3>
        <div className="metric-grid">
          <Metric label="Tasks" value={`${approvedTasks}/${totalTasks}`} status={approvedTasks === totalTasks ? 'success' : 'progress'} />
          <Metric label="AI Runs" value={aiRunCount} status={aiRunCount > 0 ? 'success' : 'neutral'} />
          <Metric label="Artifacts" value={artifactCount} status={artifactCount > 0 ? 'success' : 'neutral'} />
          <Metric label="Validations" value={`${passed}/${validations.length}`} status={failed === 0 ? 'success' : 'warning'} />
          <Metric label="Failed" value={failed} status={failed === 0 ? 'success' : 'error'} />
          <Metric label="Not Validated" value={notValidated} status={notValidated === 0 ? 'success' : 'warning'} />
        </div>
      </div>

      <div className="dashboard-project__help">
        <p className="help-text">
          📌 <strong>Tip:</strong> Follow the workflow: Requirement → Plan → Tasks → AI Runs → Artifacts → Validate → Final Report
        </p>
      </div>
    </div>
  )
}

function Metric({ label, value, status }: { label: string; value: string | number; status: string }) {
  return (
    <div className={`metric-card metric-card--${status}`}>
      <div className="metric-card__value">{value}</div>
      <div className="metric-card__label">{label}</div>
    </div>
  )
}

function WorkflowStep({ number, icon, title, description }: { number: number; icon: string; title: string; description: string }) {
  return (
    <div className="workflow-step">
      <div className="workflow-step__number">{number}</div>
      <div className="workflow-step__icon">{icon}</div>
      <h4 className="workflow-step__title">{title}</h4>
      <p className="workflow-step__description">{description}</p>
    </div>
  )
}
