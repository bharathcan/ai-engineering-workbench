import { useState } from 'react'
import { RequirementApiError } from '../api/requirements'
import {
  decideTask,
  decideAiRun,
  generateArtifacts,
  requestAiAssist,
  type AIAssistRequestType,
  type EngineeringTask,
} from '../api/tasks'
import '../components/EngineeringPlanPanel.css'
import '../components/TasksGrid.css'
import '../components/TaskDetail.css'
import { TasksGrid } from '../components/TasksGrid'
import type { ProjectData } from '../hooks/useProjectData'

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

export function TasksScreen({
  project,
  onChanged,
}: {
  project: ProjectData | null
  onChanged: () => void
}) {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  if (!project) {
    return (
      <section className="screen">
        <h2>Tasks</h2>
        <p className="app-shell__empty">Select a project first.</p>
      </section>
    )
  }

  if (!project.plan || project.plan.status !== 'GENERATED') {
    return (
      <section className="screen">
        <h2>Tasks</h2>
        <p className="app-shell__empty">
          No engineering plan generated yet. Go to the Engineering Plan screen first.
        </p>
      </section>
    )
  }

  const tasks = project.plan.tasks
  const selectedTask = tasks.find((t) => t.id === selectedTaskId) ?? tasks[0] ?? null

  return (
    <section className="screen">
      <h2>Task Execution</h2>
      <TasksGrid
        tasks={tasks}
        selectedTaskId={selectedTaskId}
        onSelectTask={setSelectedTaskId}
      />
      <div style={{ marginTop: '2rem', paddingTop: '2rem', borderTop: '1px solid #e5e7eb' }}>
        {selectedTask ? (
          <>
            <h3 style={{ marginBottom: '1.5rem' }}>Task Details</h3>
            <TaskDetail key={selectedTask.id} task={selectedTask} onChanged={onChanged} />
          </>
        ) : (
          <p style={{ color: '#6b7280', fontStyle: 'italic' }}>Select a task to view details</p>
        )}
      </div>
    </section>
  )
}

function TaskDetail({ task, onChanged }: { task: EngineeringTask; onChanged: () => void }) {
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
      await decideTask(
        task.id,
        decision,
        decision === 'ACCEPT' ? undefined : rationale,
        decision === 'MODIFY' ? changes : undefined,
      )
      setPendingDecision(null)
      onChanged()
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <article className="task-detail">
      <div className="task-detail__header">
        <div>
          <span className="task-detail__id">{task.id}</span>
        </div>
        <div className="task-detail__badges">
          <span className="task-detail__badge task-detail__badge--type">{task.type}</span>
          <span className={`task-detail__badge task-detail__badge--status`}>
            {task.review_status}
          </span>
        </div>
      </div>

      <h2 className="task-detail__title">{task.title}</h2>
      <div className="task-detail__description">{task.description}</div>

      <div className="task-detail__meta-grid">
        <div className="task-detail__meta">
          <span className="task-detail__meta-label">Status</span>
          <span className="task-detail__meta-value">{task.status}</span>
        </div>
        <div className="task-detail__meta">
          <span className="task-detail__meta-label">AI Type</span>
          <span className="task-detail__meta-value">{task.ai_assistance_type}</span>
        </div>
        <div className="task-detail__meta">
          <span className="task-detail__meta-label">Priority</span>
          <span className="task-detail__meta-value"><strong>#{task.sequence}</strong></span>
        </div>
      </div>

      {(task.requirement_refs.length > 0 || task.dependencies.length > 0) && (
        <div className="task-detail__section">
          <span className="task-detail__section-title">Dependencies & References</span>
          <div className="task-detail__meta-grid">
            {task.requirement_refs.length > 0 && (
              <div className="task-detail__meta">
                <span className="task-detail__meta-label">Requirements</span>
                <span className="task-detail__meta-value">
                  {task.requirement_refs.map((r, i) => (
                    <span key={i}>
                      <strong>{r}</strong>
                      {i < task.requirement_refs.length - 1 ? ', ' : ''}
                    </span>
                  ))}
                </span>
              </div>
            )}
            {task.dependencies.length > 0 && (
              <div className="task-detail__meta">
                <span className="task-detail__meta-label">Blocked By</span>
                <span className="task-detail__meta-value">
                  {task.dependencies.map((d, i) => (
                    <span key={i}>
                      <strong>{d}</strong>
                      {i < task.dependencies.length - 1 ? ', ' : ''}
                    </span>
                  ))}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="task-detail__section">
        <span className="task-detail__section-title">Acceptance Criteria</span>
        <ul className="task-detail__list">
          {task.acceptance_criteria.map((c, i) => (
            <li key={i} className="task-detail__list-item" data-number={i + 1}>
              {c}
            </li>
          ))}
        </ul>
      </div>

      {task.risks.length > 0 && (
        <div className="task-detail__section">
          <span className="task-detail__section-title">Risks & Mitigations</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {task.risks.map((r) => (
              <div key={r.id} className="task-detail__risk">
                <span className="task-detail__risk-impact">[{r.impact}]</span>
                {r.description}
              </div>
            ))}
          </div>
        </div>
      )}

      {!alreadyDecided && (
        <p className="badge badge--ai" style={{ marginTop: '0.5rem' }}>
          AI-suggested decomposition — requires an engineer decision below before execution can
          begin
        </p>
      )}

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

      {task.status === 'APPROVED' && <AIAssistanceSection task={task} onChanged={onChanged} />}
    </article>
  )
}

function AIAssistanceSection({
  task,
  onChanged,
}: {
  task: EngineeringTask
  onChanged: () => void
}) {
  const [assistanceType, setAssistanceType] = useState<AIAssistRequestType>('CODE_GENERATION')
  const [instructions, setInstructions] = useState('')
  const [requesting, setRequesting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const latestRun = task.ai_runs.length > 0 ? task.ai_runs[task.ai_runs.length - 1] : null
  const latestDecision =
    latestRun && latestRun.decisions.length > 0
      ? latestRun.decisions[latestRun.decisions.length - 1]
      : null
  const awaitingRevision = latestDecision?.decision === 'MODIFY'

  const submitRequest = async () => {
    setRequesting(true)
    setError(null)
    try {
      await requestAiAssist(task.id, assistanceType, instructions || undefined)
      setInstructions('')
      onChanged()
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setRequesting(false)
    }
  }

  const submitDecision = async (runId: string, decision: 'ACCEPT' | 'MODIFY' | 'REJECT') => {
    setRequesting(true)
    setError(null)
    try {
      await decideAiRun(runId, decision)
      onChanged()
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setRequesting(false)
    }
  }

  const generateAndNotify = async (runId: string) => {
    setRequesting(true)
    setError(null)
    try {
      await generateArtifacts(runId)
      onChanged()
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Failed to generate artifacts.')
    } finally {
      setRequesting(false)
    }
  }

  return (
    <div className="ai-assist">
      <h5>AI Assistance ({task.ai_runs.length} run(s) so far)</h5>
      <p style={{ fontSize: '0.85rem', color: '#6b7280' }}>
        Full run history, prompts, and responses are on the AI Runs screen. Generated artifacts
        are on the Artifacts screen.
      </p>

      {task.ai_runs.length > 0 && (
        <div className="ai-assist__runs" style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid #e5e7eb' }}>
          {task.ai_runs.map((run) => (
            <div key={run.id} className="ai-run-card" style={{ marginBottom: '1rem', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '4px', backgroundColor: '#f9fafb' }}>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <strong>{run.id}</strong>
                <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>{run.assistance_type}</span>
                <span style={{ fontSize: '0.85rem', color: '#059669' }}>Confidence: {run.response?.confidence || 'N/A'}</span>
              </div>
              {run.response?.summary && <p style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>{run.response.summary}</p>}
              <p style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: '0.5rem' }}>Status: {run.status}</p>
              {!run.decisions || run.decisions.length === 0 ? (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button type="button" style={{ padding: '0.375rem 0.75rem', fontSize: '0.875rem' }} disabled={requesting} onClick={() => submitDecision(run.id, 'ACCEPT')}>
                    Accept
                  </button>
                  <button type="button" style={{ padding: '0.375rem 0.75rem', fontSize: '0.875rem' }} disabled={requesting} onClick={() => submitDecision(run.id, 'MODIFY')}>
                    Modify
                  </button>
                  <button type="button" style={{ padding: '0.375rem 0.75rem', fontSize: '0.875rem' }} disabled={requesting} onClick={() => submitDecision(run.id, 'REJECT')}>
                    Reject
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <p style={{ fontSize: '0.85rem', color: '#6b7280', margin: 0 }}>Decision: {run.decisions[run.decisions.length - 1].decision}</p>
                  {run.decisions[run.decisions.length - 1].decision === 'ACCEPT' && (
                    <button type="button" style={{ padding: '0.375rem 0.75rem', fontSize: '0.875rem' }} disabled={requesting} onClick={() => generateAndNotify(run.id)}>
                      Generate Artifacts
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {error && <p className="ai-assist__error">{error}</p>}

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
        <label>Instructions {awaitingRevision ? '(what should change?)' : '(optional)'}</label>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          rows={2}
          placeholder="Optional — additional instructions for this request."
        />
        <button type="button" disabled={requesting} onClick={submitRequest}>
          {requesting ? 'Requesting…' : awaitingRevision ? 'Request Revision' : 'Request AI Assistance'}
        </button>
      </div>
    </div>
  )
}
