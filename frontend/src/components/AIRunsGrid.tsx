import type { ProjectData } from '../hooks/useProjectData'

interface AIRunCardProps {
  run: any
  task: any
  isSelected: boolean
  onSelect: () => void
  artifacts: any[]
}

export function AIRunCard({ run, task, isSelected, onSelect, artifacts }: AIRunCardProps) {
  const decision = run.decisions.length > 0 ? run.decisions[run.decisions.length - 1] : null

  return (
    <button
      className={`ai-run-card ${isSelected ? 'ai-run-card--selected' : ''}`}
      onClick={onSelect}
    >
      <div className="ai-run-card__header">
        <span className="ai-run-card__id">{run.id}</span>
        <span className={`ai-run-card__status ai-run-card__status--${run.status.toLowerCase()}`}>
          {run.status}
        </span>
      </div>

      <h4 className="ai-run-card__type">{run.assistance_type}</h4>

      <div className="ai-run-card__task">
        <strong>{task.id}</strong>
        <p>{task.title}</p>
      </div>

      <div className="ai-run-card__summary">
        {run.response?.summary}
      </div>

      <div className="ai-run-card__footer">
        <div className="ai-run-card__confidence">
          Confidence: <strong>{run.response?.confidence || 'N/A'}</strong>
        </div>
        {decision && (
          <div className={`ai-run-card__decision ai-run-card__decision--${decision.decision.toLowerCase()}`}>
            {decision.decision}
          </div>
        )}
        {!decision && (
          <div className="ai-run-card__decision ai-run-card__decision--pending">
            PENDING
          </div>
        )}
      </div>

      {artifacts.length > 0 && (
        <div className="ai-run-card__artifacts">
          {artifacts.length} artifact{artifacts.length !== 1 ? 's' : ''}
        </div>
      )}
    </button>
  )
}

export function AIRunsGrid({
  runs,
  selectedRunId,
  onSelectRun,
  project,
}: {
  runs: Array<{ task: any; run: any }>
  selectedRunId: string | null
  onSelectRun: (runId: string) => void
  project: ProjectData
}) {
  return (
    <div className="ai-runs-grid">
      {runs.map(({ task, run }) => {
        const artifacts = (project.artifactsByTaskId[task.id] ?? []).filter(
          (a) => a.ai_run_id === run.id,
        )
        return (
          <AIRunCard
            key={run.id}
            run={run}
            task={task}
            isSelected={selectedRunId === run.id}
            onSelect={() => onSelectRun(run.id)}
            artifacts={artifacts}
          />
        )
      })}
    </div>
  )
}
