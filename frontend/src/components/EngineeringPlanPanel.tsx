import { useState } from 'react'
import './EngineeringPlanPanel.css'
import { decideArtifact, generateArtifacts, type Artifact } from '../api/artifacts'
import { RequirementApiError } from '../api/requirements'
import {
  decideAiRun,
  decideTask,
  generatePlan,
  getTask,
  requestAiAssist,
  type AIAssistRequestType,
  type AIRun,
  type EngineeringPlan,
  type EngineeringTask,
} from '../api/tasks'
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

const VALIDATION_LABELS: Record<ValidationType, string> = {
  UNIT_TEST: 'Unit Tests',
  INTEGRATION_TEST: 'Integration',
  API_CONTRACT: 'API Contract',
  STATIC_ANALYSIS: 'Static Analysis',
  SECURITY: 'Security',
  PERFORMANCE: 'Performance',
  BUILD: 'Build',
}

function statusIcon(status: Validation['status'] | undefined): string {
  if (status === 'PASSED') return '✓'
  if (status === 'FAILED') return '✗'
  if (status === 'NOT_VALIDATED') return '⚠'
  return '○'
}

const ASSISTANCE_TYPES: AIAssistRequestType[] = [
  'DESIGN',
  'CODE_GENERATION',
  'DEBUGGING',
  'REFACTORING',
  'TEST_GENERATION',
  'DOCUMENTATION',
  'SECURITY_REVIEW',
  'PERFORMANCE_REVIEW',
]

type PlanState =
  | { phase: 'idle' }
  | { phase: 'generating' }
  | { phase: 'done'; plan: EngineeringPlan }
  | { phase: 'error'; message: string }

export function EngineeringPlanPanel({ requirementId }: { requirementId: string }) {
  const [state, setState] = useState<PlanState>({ phase: 'idle' })

  const handleGenerate = async () => {
    setState({ phase: 'generating' })
    try {
      const plan = await generatePlan(requirementId)
      setState({ phase: 'done', plan })
    } catch (err) {
      const message = err instanceof RequirementApiError ? err.message : 'Something went wrong.'
      setState({ phase: 'error', message })
    }
  }

  const handleTaskUpdated = (updatedTask: EngineeringTask) => {
    if (state.phase !== 'done') return
    setState({
      phase: 'done',
      plan: {
        ...state.plan,
        tasks: state.plan.tasks.map((t) => (t.id === updatedTask.id ? updatedTask : t)),
      },
    })
  }

  return (
    <section className="plan-panel">
      <button
        type="button"
        className="plan-panel__generate-button"
        onClick={handleGenerate}
        disabled={state.phase === 'generating'}
      >
        {state.phase === 'generating' ? 'Generating…' : 'Generate Engineering Plan'}
      </button>

      {state.phase === 'error' && <p className="plan-panel__error">{state.message}</p>}

      {state.phase === 'done' && state.plan.status === 'BLOCKED' && (
        <div className="plan-panel__blocked">
          <h3>PLAN BLOCKED</h3>
          <p>
            <strong>Reason:</strong> {state.plan.blocked_reason}
          </p>
        </div>
      )}

      {state.phase === 'done' && state.plan.status === 'GENERATED' && (
        <div className="plan-panel__plan">
          <h2>Engineering Plan</h2>
          <p className="plan-panel__summary">{state.plan.summary}</p>
          {state.plan.tasks.map((task) => (
            <TaskCard key={task.id} task={task} onDecided={handleTaskUpdated} />
          ))}
        </div>
      )}
    </section>
  )
}

function TaskCard({
  task,
  onDecided,
}: {
  task: EngineeringTask
  onDecided: (task: EngineeringTask) => void
}) {
  const [pendingDecision, setPendingDecision] = useState<'MODIFY' | 'REJECT' | null>(null)
  const [rationale, setRationale] = useState('')
  const [changes, setChanges] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const alreadyDecided = task.review_status !== 'PENDING'

  const submit = async (decision: 'ACCEPT' | 'MODIFY' | 'REJECT') => {
    setSubmitting(true)
    setError(null)
    try {
      const updated = await decideTask(
        task.id,
        decision,
        decision === 'ACCEPT' ? undefined : rationale,
        decision === 'MODIFY' ? changes : undefined,
      )
      onDecided(updated)
      setPendingDecision(null)
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <article className="task-card">
      <header className="task-card__header">
        <strong>{task.id}</strong>
        <span className="task-card__type">{task.type}</span>
      </header>
      <h4>{task.title}</h4>
      <p>{task.description}</p>

      <p className="task-card__meta">
        <strong>Requirement:</strong> {task.requirement_refs.join(', ') || 'None'}
      </p>
      <p className="task-card__meta">
        <strong>Dependencies:</strong> {task.dependencies.join(', ') || 'None'}
      </p>
      <p className="task-card__meta">
        <strong>AI Assistance:</strong> {task.ai_assistance_type}
      </p>

      <div className="task-card__criteria">
        <strong>Acceptance Criteria:</strong>
        <ul>
          {task.acceptance_criteria.map((c, i) => (
            <li key={i}>☐ {c}</li>
          ))}
        </ul>
      </div>

      <div className="task-card__review">
        <strong>Review:</strong>{' '}
        <span className={`review-status review-status--${task.review_status.toLowerCase()}`}>
          {task.review_status} ({task.status})
        </span>
      </div>

      {!alreadyDecided && (
        <div className="task-card__actions">
          {pendingDecision === null && (
            <>
              <button type="button" disabled={submitting} onClick={() => submit('ACCEPT')}>
                Accept
              </button>
              <button type="button" disabled={submitting} onClick={() => setPendingDecision('MODIFY')}>
                Modify
              </button>
              <button type="button" disabled={submitting} onClick={() => setPendingDecision('REJECT')}>
                Reject
              </button>
            </>
          )}

          {pendingDecision !== null && (
            <div className="task-card__decision-form">
              <textarea
                placeholder="Rationale (required)"
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                rows={2}
              />
              {pendingDecision === 'MODIFY' && (
                <textarea
                  placeholder="Requested changes (required)"
                  value={changes}
                  onChange={(e) => setChanges(e.target.value)}
                  rows={2}
                />
              )}
              <div className="task-card__decision-form-actions">
                <button type="button" disabled={submitting} onClick={() => submit(pendingDecision)}>
                  Submit {pendingDecision === 'MODIFY' ? 'Modify' : 'Reject'}
                </button>
                <button type="button" disabled={submitting} onClick={() => setPendingDecision(null)}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {error && <p className="task-card__error">{error}</p>}
        </div>
      )}

      {task.status === 'APPROVED' && (
        <AIAssistanceSection task={task} onTaskUpdated={onDecided} />
      )}
    </article>
  )
}

function AIAssistanceSection({
  task,
  onTaskUpdated,
}: {
  task: EngineeringTask
  onTaskUpdated: (task: EngineeringTask) => void
}) {
  const [assistanceType, setAssistanceType] = useState<AIAssistRequestType>('CODE_GENERATION')
  const [instructions, setInstructions] = useState('')
  const [revisionText, setRevisionText] = useState('')
  const [requesting, setRequesting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const latestRun = task.ai_runs.length > 0 ? task.ai_runs[task.ai_runs.length - 1] : null
  const latestDecision =
    latestRun && latestRun.decisions.length > 0
      ? latestRun.decisions[latestRun.decisions.length - 1]
      : null
  const awaitingRevision = latestDecision?.decision === 'MODIFY'

  const refreshTask = async () => {
    const updated = await getTask(task.id)
    onTaskUpdated(updated)
  }

  const submitRequest = async (customInstructions: string) => {
    setRequesting(true)
    setError(null)
    try {
      await requestAiAssist(task.id, assistanceType, customInstructions || undefined)
      await refreshTask()
      setInstructions('')
      setRevisionText('')
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setRequesting(false)
    }
  }

  return (
    <div className="ai-assist">
      <h5>AI Assistance</h5>

      {task.ai_runs.length > 0 && (
        <div className="ai-assist__history">
          <strong>AI Run History</strong>
          <ul>
            {task.ai_runs.map((run) => (
              <li key={run.id}>
                <span className="ai-assist__history-id">{run.id}</span> {run.assistance_type} —{' '}
                {runHistoryLabel(run)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {latestRun && <AIRunCard run={latestRun} onDecided={refreshTask} />}

      {error && <p className="ai-assist__error">{error}</p>}

      {awaitingRevision ? (
        <div className="ai-assist__request-form">
          <label>What should be changed?</label>
          <textarea
            value={revisionText}
            onChange={(e) => setRevisionText(e.target.value)}
            rows={2}
            placeholder="Describe what the next attempt should do differently…"
          />
          <button
            type="button"
            disabled={requesting || revisionText.trim().length === 0}
            onClick={() => submitRequest(revisionText)}
          >
            {requesting ? 'Requesting…' : 'Request Revision'}
          </button>
        </div>
      ) : (
        <div className="ai-assist__request-form">
          <label>Type</label>
          <select
            value={assistanceType}
            onChange={(e) => setAssistanceType(e.target.value as AIAssistRequestType)}
          >
            {ASSISTANCE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <label>Instructions</label>
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            rows={2}
            placeholder="Optional — additional instructions for this request."
          />
          <button type="button" disabled={requesting} onClick={() => submitRequest(instructions)}>
            {requesting ? 'Requesting…' : 'Request AI Assistance'}
          </button>
        </div>
      )}
    </div>
  )
}

function runHistoryLabel(run: AIRun): string {
  if (run.status === 'FAILED') return 'FAILED'
  if (run.decisions.length === 0) return 'PENDING REVIEW'
  const decision = run.decisions[run.decisions.length - 1].decision
  return decision === 'ACCEPT' ? 'ACCEPTED' : decision === 'MODIFY' ? 'MODIFIED' : 'REJECTED'
}

function AIRunCard({ run, onDecided }: { run: AIRun; onDecided: () => void }) {
  const [pendingDecision, setPendingDecision] = useState<'MODIFY' | 'REJECT' | null>(null)
  const [rationale, setRationale] = useState('')
  const [changes, setChanges] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const alreadyDecided = run.decisions.length > 0
  const wasAccepted =
    run.decisions.length > 0 && run.decisions[run.decisions.length - 1].decision === 'ACCEPT'
  const needsReview =
    run.status === 'COMPLETED' && run.response !== null && run.response.confidence !== 'HIGH'

  const submit = async (decision: 'ACCEPT' | 'MODIFY' | 'REJECT') => {
    setSubmitting(true)
    setError(null)
    try {
      await decideAiRun(
        run.id,
        decision,
        decision === 'ACCEPT' ? undefined : rationale,
        decision === 'MODIFY' ? changes : undefined,
      )
      onDecided()
      setPendingDecision(null)
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  if (run.status === 'FAILED') {
    return (
      <div className="ai-run-card ai-run-card--failed">
        <strong>{run.id}</strong> failed: {run.error}
      </div>
    )
  }

  const rec = run.response
  if (!rec) return null

  return (
    <div className="ai-run-card">
      <header className="ai-run-card__header">
        <strong>{run.id}</strong>
        <span className={`confidence-badge confidence-badge--${rec.confidence.toLowerCase()}`}>
          Confidence: {rec.confidence}
        </span>
      </header>

      <p>
        <strong>Summary:</strong> {rec.summary}
      </p>
      <p>
        <strong>Approach:</strong> {rec.approach}
      </p>
      <p>
        <strong>Files:</strong> {rec.files_to_change.join(', ') || 'None'}
      </p>
      <p>
        <strong>Tests:</strong> {rec.tests_to_add.join(', ') || 'None'}
      </p>
      <p>
        <strong>Risks:</strong> {rec.risks.join('; ') || 'None'}
      </p>

      {needsReview && <p className="ai-run-card__warning">⚠ ENGINEERING REVIEW REQUIRED</p>}

      {!alreadyDecided && (
        <div className="task-card__actions">
          {pendingDecision === null && (
            <>
              <button type="button" disabled={submitting} onClick={() => submit('ACCEPT')}>
                Accept
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={() => setPendingDecision('MODIFY')}
              >
                Modify
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={() => setPendingDecision('REJECT')}
              >
                Reject
              </button>
            </>
          )}

          {pendingDecision !== null && (
            <div className="task-card__decision-form">
              <textarea
                placeholder="Rationale (required)"
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                rows={2}
              />
              {pendingDecision === 'MODIFY' && (
                <textarea
                  placeholder="Requested changes (required)"
                  value={changes}
                  onChange={(e) => setChanges(e.target.value)}
                  rows={2}
                />
              )}
              <div className="task-card__decision-form-actions">
                <button type="button" disabled={submitting} onClick={() => submit(pendingDecision)}>
                  Submit {pendingDecision === 'MODIFY' ? 'Modify' : 'Reject'}
                </button>
                <button type="button" disabled={submitting} onClick={() => setPendingDecision(null)}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {error && <p className="task-card__error">{error}</p>}
        </div>
      )}

      {wasAccepted && <ArtifactSection aiRunId={run.id} />}
    </div>
  )
}

function ArtifactSection({ aiRunId }: { aiRunId: string }) {
  const [artifacts, setArtifacts] = useState<Artifact[] | null>(null)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    setGenerating(true)
    setError(null)
    try {
      const result = await generateArtifacts(aiRunId)
      setArtifacts(result)
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setGenerating(false)
    }
  }

  const handleArtifactUpdated = (updated: Artifact) => {
    setArtifacts((prev) => (prev ? prev.map((a) => (a.id === updated.id ? updated : a)) : prev))
  }

  return (
    <div className="artifact-section">
      {artifacts === null && (
        <button type="button" disabled={generating} onClick={handleGenerate}>
          {generating ? 'Generating…' : 'Generate Artifacts'}
        </button>
      )}
      {error && <p className="task-card__error">{error}</p>}
      {artifacts?.map((artifact) => (
        <ArtifactCard key={artifact.id} artifact={artifact} onDecided={handleArtifactUpdated} />
      ))}
    </div>
  )
}

function ArtifactCard({
  artifact,
  onDecided,
}: {
  artifact: Artifact
  onDecided: (artifact: Artifact) => void
}) {
  const [showContent, setShowContent] = useState(false)
  const [rationale, setRationale] = useState('')
  const [pendingReject, setPendingReject] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const alreadyDecided = artifact.status !== 'PENDING_REVIEW'

  const submit = async (decision: 'ACCEPT' | 'REJECT') => {
    setSubmitting(true)
    setError(null)
    try {
      const updated = await decideArtifact(
        artifact.id,
        decision,
        decision === 'REJECT' ? rationale : undefined,
      )
      onDecided(updated)
      setPendingReject(false)
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <article className="artifact-card">
      <header className="artifact-card__header">
        <strong>{artifact.id}</strong>
        <span className="task-card__type">{artifact.artifact_type}</span>
        <span>v{artifact.version}</span>
        <span className={`review-status review-status--${artifact.status.toLowerCase()}`}>
          {artifact.status}
        </span>
      </header>
      <p className="artifact-card__path">{artifact.path}</p>
      <p>{artifact.description}</p>
      {artifact.supersedes_artifact_id && (
        <p className="task-card__meta">Supersedes: {artifact.supersedes_artifact_id}</p>
      )}

      <button type="button" onClick={() => setShowContent((v) => !v)}>
        {showContent ? 'Hide' : 'Show'} {artifact.diff ? 'Diff' : 'Content'}
      </button>
      {showContent && (
        <pre className="artifact-card__content">{artifact.diff ?? artifact.content}</pre>
      )}

      {!alreadyDecided && (
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
      )}

      {artifact.status === 'APPROVED' && <ValidationDashboard artifactId={artifact.id} />}
    </article>
  )
}

function ValidationDashboard({ artifactId }: { artifactId: string }) {
  const [validations, setValidations] = useState<Record<ValidationType, Validation | undefined>>(
    {} as Record<ValidationType, Validation | undefined>,
  )
  const [running, setRunning] = useState<ValidationType | null>(null)
  const [expanded, setExpanded] = useState<ValidationType | null>(null)
  const [error, setError] = useState<string | null>(null)

  const runValidation = async (type: ValidationType) => {
    setRunning(type)
    setError(null)
    try {
      const result = await validateArtifact(artifactId, type)
      setValidations((prev) => ({ ...prev, [type]: result }))
      setExpanded(type)
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setRunning(null)
    }
  }

  return (
    <div className="validation-dashboard">
      <strong>Validation</strong>
      <ul className="validation-dashboard__list">
        {VALIDATION_TYPES.map((type) => {
          const validation = validations[type]
          return (
            <li key={type}>
              <button
                type="button"
                className="validation-dashboard__item"
                disabled={running === type}
                onClick={() =>
                  validation ? setExpanded(expanded === type ? null : type) : runValidation(type)
                }
              >
                <span className={`validation-icon validation-icon--${(validation?.status ?? 'unrun').toLowerCase()}`}>
                  {running === type ? '…' : statusIcon(validation?.status)}
                </span>
                {VALIDATION_LABELS[type]}
              </button>
              {expanded === type && validation && (
                <div className="validation-dashboard__evidence">
                  <p>
                    <strong>Command:</strong> {validation.command}
                  </p>
                  <p>
                    <strong>Evidence:</strong> {validation.evidence}
                  </p>
                  {validation.error && (
                    <p className="task-card__error">
                      <strong>Error:</strong> {validation.error}
                    </p>
                  )}
                  <button type="button" onClick={() => runValidation(type)} disabled={running === type}>
                    Re-run
                  </button>
                </div>
              )}
            </li>
          )
        })}
      </ul>
      {error && <p className="task-card__error">{error}</p>}
    </div>
  )
}
