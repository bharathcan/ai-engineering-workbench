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
      <section className="screen">
        <h2>Dashboard</h2>
        <p className="app-shell__empty">
          No project selected. Choose a project above, or go to{' '}
          <button type="button" onClick={() => onNavigate('requirement')} className="link-button">
            Requirement
          </button>{' '}
          to start a new one.
        </p>
      </section>
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
    <section className="screen">
      <h2>Project Dashboard</h2>
      <p>
        <strong>Requirement:</strong> {requirement.text}
      </p>
      <p>
        <strong>Current stage:</strong> {stage.label}
      </p>
      <StageFlow currentIndex={stage.index} />

      {plan?.status === 'BLOCKED' && (
        <p className="badge badge--blocked">BLOCKED — {plan.blocked_reason}</p>
      )}

      <div className="metric-grid">
        <Metric label="Tasks (approved / total)" value={`${approvedTasks} / ${totalTasks}`} />
        <Metric label="AI Runs" value={aiRunCount} />
        <Metric label="Artifacts" value={artifactCount} />
        <Metric label="Validations Passed" value={passed} />
        <Metric label="Validations Failed" value={failed} />
        <Metric label="Not Validated" value={notValidated} />
      </div>

      <p className="app-shell__empty" style={{ textAlign: 'left', padding: 0 }}>
        Example flow: Requirement → Plan → Execute → Review → Artifacts → Validate → Report.
        This dashboard infers the current stage from what data exists so far — it is not a
        stored field, only a display convenience.
      </p>
    </section>
  )
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric-card">
      <div className="metric-card__value">{value}</div>
      <div className="metric-card__label">{label}</div>
    </div>
  )
}
