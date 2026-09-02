import { flattenAiRuns, type ProjectData } from '../hooks/useProjectData'
import { maskSecrets } from '../utils/maskSecrets'
import '../components/EngineeringPlanPanel.css'

export function AIRunsScreen({ project }: { project: ProjectData | null }) {
  if (!project) {
    return (
      <section className="screen">
        <h2>AI Runs</h2>
        <p className="app-shell__empty">Select a project first.</p>
      </section>
    )
  }

  const runs = flattenAiRuns(project.plan)

  return (
    <section className="screen">
      <h2>AI Runs</h2>
      <p className="badge badge--ai">
        Every entry here is an AI-generated engineering input, not automatically trusted code or
        an approved decision. See the Engineer Decision on each run.
      </p>

      {runs.length === 0 && <p className="app-shell__empty">No AI runs yet for this project.</p>}

      <div className="flat-list screen-section">
        {runs.map(({ task, run }) => {
          const decision = run.decisions.length > 0 ? run.decisions[run.decisions.length - 1] : null
          const relatedArtifacts = (project.artifactsByTaskId[task.id] ?? []).filter(
            (a) => a.ai_run_id === run.id,
          )
          return (
            <article key={run.id} className="flat-list-item">
              <div className="flat-list-item__header">
                <strong>{run.id}</strong>
                <span className="task-card__type">{run.assistance_type}</span>
                <span
                  className={
                    'badge ' + (run.status === 'COMPLETED' ? 'badge--passed' : 'badge--failed')
                  }
                >
                  {run.status}
                </span>
              </div>
              <p className="flat-list-item__meta">
                <strong>Task:</strong> {task.id} — {task.title}
              </p>
              <p className="flat-list-item__meta">
                <strong>Timestamp:</strong> {run.created_at}
              </p>
              <p className="flat-list-item__meta">
                <strong>Provider / Model:</strong> {run.provider} / {run.model}
              </p>
              {run.instructions && (
                <p className="flat-list-item__meta">
                  <strong>Instructions:</strong> {maskSecrets(run.instructions)}
                </p>
              )}

              <details>
                <summary>Prompt sent to the AI provider</summary>
                <pre className="artifact-card__content">{maskSecrets(run.prompt)}</pre>
              </details>

              {run.status === 'FAILED' && (
                <p className="task-card__error">
                  <strong>Error:</strong> {run.error}
                </p>
              )}

              {run.response && (
                <details open>
                  <summary>AI response</summary>
                  <p>
                    <strong>Summary:</strong> {maskSecrets(run.response.summary)}
                  </p>
                  <p>
                    <strong>Approach:</strong> {maskSecrets(run.response.approach)}
                  </p>
                  <p>
                    <strong>Confidence:</strong> {run.response.confidence}
                  </p>
                  <p>
                    <strong>Files to change:</strong>{' '}
                    {run.response.files_to_change.join(', ') || 'None'}
                  </p>
                  <p>
                    <strong>Risks noted by the AI:</strong> {run.response.risks.join('; ') || 'None'}
                  </p>
                </details>
              )}

              <p className="flat-list-item__meta">
                <strong>Engineer decision:</strong>{' '}
                {decision ? (
                  <span className={`review-status review-status--${decision.decision.toLowerCase()}`}>
                    {decision.decision}
                    {decision.rationale ? ` — ${decision.rationale}` : ''}
                  </span>
                ) : (
                  <span className="badge badge--not-validated">PENDING ENGINEER REVIEW</span>
                )}
              </p>
              <p className="flat-list-item__meta">
                <strong>Related artifact(s):</strong>{' '}
                {relatedArtifacts.length > 0
                  ? relatedArtifacts.map((a) => a.id).join(', ')
                  : 'None generated from this run'}
              </p>
            </article>
          )
        })}
      </div>
    </section>
  )
}
