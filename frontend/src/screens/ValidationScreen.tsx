import { useState } from 'react'
import { RequirementApiError } from '../api/requirements'
import '../components/EngineeringPlanPanel.css'
import { flattenValidations, type ProjectData } from '../hooks/useProjectData'
import { validateArtifact, type Validation, type ValidationType } from '../api/validations'

const VALIDATION_TYPES: ValidationType[] = [
  'UNIT_TEST',
  'INTEGRATION_TEST',
  'API_CONTRACT',
  'STATIC_ANALYSIS',
  'SECURITY',
  'PERFORMANCE',
  'BUILD',
]

function statusBadgeClass(status: Validation['status']): string {
  if (status === 'PASSED') return 'badge badge--passed'
  if (status === 'FAILED') return 'badge badge--failed'
  if (status === 'NOT_VALIDATED') return 'badge badge--not-validated'
  return 'badge'
}

export function ValidationScreen({
  project,
  onChanged,
}: {
  project: ProjectData | null
  onChanged: () => void
}) {
  const [runningFor, setRunningFor] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!project) {
    return (
      <section className="screen">
        <h2>Validation</h2>
        <p className="app-shell__empty">Select a project first.</p>
      </section>
    )
  }

  const validations = flattenValidations(
    project.plan,
    project.artifactsByTaskId,
    project.validationsByArtifactId,
  )

  const runNewValidation = async (artifactId: string, type: ValidationType) => {
    setRunningFor(`${artifactId}:${type}`)
    setError(null)
    try {
      await validateArtifact(artifactId, type)
      onChanged()
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setRunningFor(null)
    }
  }

  const approvedArtifactsWithoutRun = flattenArtifactsApproved(project)

  return (
    <section className="screen">
      <h2>Validation</h2>
      <p className="badge badge--not-validated">
        NOT_VALIDATED means the validation was never run — it is distinct from PASSED and must
        never be presented as a pass.
      </p>

      {error && <p className="task-card__error">{error}</p>}

      {approvedArtifactsWithoutRun.length > 0 && (
        <div className="screen-section">
          <h4>Run a new validation</h4>
          {approvedArtifactsWithoutRun.map((artifact) => (
            <div key={artifact.id} className="flat-list-item" style={{ marginBottom: '0.75rem' }}>
              <p className="flat-list-item__meta">
                <strong>Artifact:</strong> {artifact.id} ({artifact.artifact_type})
              </p>
              <div className="task-card__actions">
                {VALIDATION_TYPES.map((type) => (
                  <button
                    key={type}
                    type="button"
                    disabled={runningFor === `${artifact.id}:${type}`}
                    onClick={() => runNewValidation(artifact.id, type)}
                  >
                    {runningFor === `${artifact.id}:${type}` ? 'Running…' : type}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {validations.length === 0 && (
        <p className="app-shell__empty">No validations recorded yet for this project.</p>
      )}

      <div className="flat-list screen-section">
        {validations.map(({ task, artifact, validation }) => (
          <article key={validation.id} className="flat-list-item">
            <div className="flat-list-item__header">
              <strong>{validation.id}</strong>
              <span className="task-card__type">{validation.validation_type}</span>
              <span className={statusBadgeClass(validation.status)}>{validation.status}</span>
            </div>
            <p className="flat-list-item__meta">
              <strong>Task / Artifact:</strong> {task.id} / {artifact.id}
            </p>
            <p className="flat-list-item__meta">
              <strong>Command:</strong> <span className="artifact-card__path">{validation.command}</span>
            </p>
            <p className="flat-list-item__meta">
              <strong>Duration:</strong> {validation.duration_ms} ms
            </p>
            <p className="flat-list-item__meta">
              <strong>Timestamp:</strong> {validation.created_at}
            </p>
            {validation.output && (
              <details>
                <summary>Output</summary>
                <pre className="artifact-card__content">{validation.output}</pre>
              </details>
            )}
            {validation.error && (
              <p className="task-card__error">
                <strong>Error:</strong> {validation.error}
              </p>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}

function flattenArtifactsApproved(project: ProjectData) {
  if (!project.plan) return []
  return project.plan.tasks.flatMap((task) =>
    (project.artifactsByTaskId[task.id] ?? []).filter((a) => a.status === 'APPROVED'),
  )
}
