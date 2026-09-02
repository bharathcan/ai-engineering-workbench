import { useState } from 'react'
import { decideArtifact, type Artifact } from '../api/artifacts'
import { RequirementApiError } from '../api/requirements'
import '../components/EngineeringPlanPanel.css'
import { flattenArtifacts, type ProjectData } from '../hooks/useProjectData'

/** The master prompt for this phase suggests artifact statuses
 * AI_RECOMMENDED / ENGINEER_REVIEW / APPROVED / REJECTED / VALIDATED. The
 * backend's actual Artifact.status enum (unchanged since Phase 6) is
 * PENDING_REVIEW / APPROVED / NEEDS_REVISION / REJECTED, and does not track
 * validation outcome on the artifact itself — that lives on separate
 * Validation records. Engineering decision: keep the backend enum
 * authoritative (renaming it would touch the data model and ~20 existing
 * backend tests for a UI-only concern) and derive a display-only label here
 * instead, folding in whether a PASSED validation exists. */
function displayStatus(artifact: Artifact, hasPassedValidation: boolean): string {
  if (artifact.status === 'PENDING_REVIEW') return 'AI_RECOMMENDED — ENGINEER_REVIEW'
  if (artifact.status === 'NEEDS_REVISION') return 'ENGINEER_REVIEW (changes requested)'
  if (artifact.status === 'REJECTED') return 'REJECTED'
  if (artifact.status === 'APPROVED') return hasPassedValidation ? 'VALIDATED' : 'APPROVED'
  return artifact.status
}

export function ArtifactsScreen({
  project,
  onChanged,
}: {
  project: ProjectData | null
  onChanged: () => void
}) {
  if (!project) {
    return (
      <section className="screen">
        <h2>Artifacts</h2>
        <p className="app-shell__empty">Select a project first.</p>
      </section>
    )
  }

  const artifacts = flattenArtifacts(project.plan, project.artifactsByTaskId)

  return (
    <section className="screen">
      <h2>Artifacts</h2>

      {artifacts.length === 0 && (
        <p className="app-shell__empty">
          No artifacts generated yet. Generate them from an accepted AI run on the Tasks screen.
        </p>
      )}

      <div className="flat-list screen-section">
        {artifacts.map(({ task, artifact }) => (
          <ArtifactCard
            key={artifact.id}
            task={task}
            artifact={artifact}
            validations={project.validationsByArtifactId[artifact.id] ?? []}
            onChanged={onChanged}
          />
        ))}
      </div>
    </section>
  )
}

function ArtifactCard({
  task,
  artifact,
  validations,
  onChanged,
}: {
  task: { id: string; title: string }
  artifact: Artifact
  validations: { status: string }[]
  onChanged: () => void
}) {
  const [showContent, setShowContent] = useState(false)
  const [rationale, setRationale] = useState('')
  const [pendingReject, setPendingReject] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const alreadyDecided = artifact.status !== 'PENDING_REVIEW'
  const hasPassedValidation = validations.some((v) => v.status === 'PASSED')

  const submit = async (decision: 'ACCEPT' | 'REJECT') => {
    setSubmitting(true)
    setError(null)
    try {
      await decideArtifact(artifact.id, decision, decision === 'REJECT' ? rationale : undefined)
      setPendingReject(false)
      onChanged()
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <article className="flat-list-item">
      <div className="flat-list-item__header">
        <strong>{artifact.id}</strong>
        <span className="task-card__type">{artifact.artifact_type}</span>
        <span>v{artifact.version}</span>
        <span className={`review-status review-status--${artifact.status.toLowerCase()}`}>
          {displayStatus(artifact, hasPassedValidation)}
        </span>
      </div>
      <p className="flat-list-item__meta">
        <strong>Task:</strong> {task.id} — {task.title}
      </p>
      <p className="flat-list-item__meta">
        <strong>AI Run:</strong> {artifact.ai_run_id}
      </p>
      <p className="flat-list-item__meta">
        <strong>Created:</strong> {artifact.created_at}
      </p>
      <p className="flat-list-item__meta">
        <strong>Path:</strong> <span className="artifact-card__path">{artifact.path}</span>
      </p>
      <p>{artifact.description}</p>
      {artifact.supersedes_artifact_id && (
        <p className="flat-list-item__meta">Supersedes: {artifact.supersedes_artifact_id}</p>
      )}
      <p className="flat-list-item__meta">
        <strong>Validations recorded:</strong> {validations.length}
        {validations.length > 0 &&
          ` (${validations.filter((v) => v.status === 'PASSED').length} passed, ${
            validations.filter((v) => v.status === 'FAILED').length
          } failed, ${validations.filter((v) => v.status === 'NOT_VALIDATED').length} not validated)`}
      </p>

      <button type="button" onClick={() => setShowContent((v) => !v)}>
        {showContent ? 'Hide' : 'Show'} {artifact.diff ? 'Diff' : 'Source'}
      </button>
      {showContent && (
        <pre className="artifact-card__content">{artifact.diff ?? artifact.content}</pre>
      )}

      {!alreadyDecided && (
        <>
          <p className="badge badge--ai" style={{ marginTop: '0.5rem' }}>
            AI-generated artifact — not yet an approved engineering artifact
          </p>
          <div className="task-card__actions">
            {!pendingReject && (
              <>
                <button type="button" disabled={submitting} onClick={() => submit('ACCEPT')}>
                  Accept
                </button>
                <button type="button" disabled={submitting} onClick={() => setPendingReject(true)}>
                  Reject
                </button>
              </>
            )}
            {pendingReject && (
              <div className="task-card__decision-form">
                <textarea
                  placeholder="Rationale (required)"
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  rows={2}
                />
                <div className="task-card__decision-form-actions">
                  <button type="button" disabled={submitting} onClick={() => submit('REJECT')}>
                    Submit Reject
                  </button>
                  <button type="button" disabled={submitting} onClick={() => setPendingReject(false)}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
            {error && <p className="task-card__error">{error}</p>}
          </div>
        </>
      )}
    </article>
  )
}
