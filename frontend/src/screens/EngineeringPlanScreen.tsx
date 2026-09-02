import { useState } from 'react'
import { RequirementApiError } from '../api/requirements'
import { generatePlan } from '../api/tasks'
import '../components/EngineeringPlanPanel.css'
import type { ProjectData } from '../hooks/useProjectData'

export function EngineeringPlanScreen({
  project,
  onPlanGenerated,
}: {
  project: ProjectData | null
  onPlanGenerated: () => void
}) {
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!project) {
    return (
      <section className="screen">
        <h2>Engineering Plan</h2>
        <p className="app-shell__empty">Select a project first.</p>
      </section>
    )
  }

  if (!project.requirement.latest_analysis) {
    return (
      <section className="screen">
        <h2>Engineering Plan</h2>
        <p className="app-shell__empty">
          This requirement has not been analyzed yet. Analyze it on the Requirement screen first.
        </p>
      </section>
    )
  }

  const handleGenerate = async () => {
    setGenerating(true)
    setError(null)
    try {
      await generatePlan(project.requirement.id)
      onPlanGenerated()
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setGenerating(false)
    }
  }

  const { plan } = project

  return (
    <section className="screen">
      <h2>Engineering Plan</h2>

      {!plan && (
        <button type="button" onClick={handleGenerate} disabled={generating}>
          {generating ? 'Generating…' : 'Generate Engineering Plan'}
        </button>
      )}
      {error && <p className="task-card__error">{error}</p>}

      {plan?.status === 'BLOCKED' && (
        <div className="plan-panel__blocked">
          <h3>PLAN BLOCKED — ENGINEER INPUT REQUIRED</h3>
          <p>
            <strong>Reason:</strong> {plan.blocked_reason}
          </p>
          <p>
            The decomposer will not guess past a high-impact ambiguity. Resolve it on the
            Requirement screen (or via the Scenarios screen for the ambiguous demo case), then
            regenerate the plan.
          </p>
        </div>
      )}

      {plan?.status === 'GENERATED' && (
        <div className="plan-panel__plan">
          <p className="plan-panel__summary">{plan.summary}</p>

          {plan.assumptions.length > 0 && (
            <div className="screen-section">
              <h4>Assumptions behind this decomposition</h4>
              <ul>
                {plan.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}

          {plan.unresolved_ambiguities.length > 0 && (
            <div className="screen-section">
              <h4>Unresolved ambiguities carried into the plan</h4>
              <ul>
                {plan.unresolved_ambiguities.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="screen-section">
            <h4>Tasks ({plan.tasks.length})</h4>
            {plan.tasks.map((task) => (
              <article key={task.id} className="task-card">
                <header className="task-card__header">
                  <strong>{task.id}</strong>
                  <span className="task-card__type">{task.type}</span>
                </header>
                <h4>
                  {task.sequence}. {task.title}
                </h4>
                <p>{task.description}</p>
                <p className="task-card__meta">
                  <strong>Traces to requirement item(s):</strong>{' '}
                  {task.requirement_refs.join(', ') || 'None'}
                </p>
                <p className="task-card__meta">
                  <strong>Depends on:</strong> {task.dependencies.join(', ') || 'None'}
                </p>
                <p className="task-card__meta">
                  <strong>Priority order:</strong> {task.sequence}
                </p>
                <div className="task-card__criteria">
                  <strong>Acceptance Criteria (Definition of Done):</strong>
                  <ul>
                    {task.acceptance_criteria.map((c, i) => (
                      <li key={i}>☐ {c}</li>
                    ))}
                  </ul>
                </div>
                <p className="task-card__review">
                  <strong>Status:</strong>{' '}
                  <span className={`review-status review-status--${task.status.toLowerCase()}`}>
                    {task.status}
                  </span>{' '}
                  · <strong>Review:</strong> {task.review_status}
                </p>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
