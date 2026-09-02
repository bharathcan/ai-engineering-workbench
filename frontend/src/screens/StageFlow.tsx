import { WORKFLOW_STAGES } from '../hooks/workflowStage'

export function StageFlow({ currentIndex }: { currentIndex: number }) {
  return (
    <div className="stage-flow" aria-label="Workflow progress">
      {WORKFLOW_STAGES.map((stage, i) => (
        <span key={stage} style={{ display: 'contents' }}>
          <span
            className={
              'stage-flow__step' + (i === currentIndex ? ' stage-flow__step--current' : '')
            }
          >
            {stage}
          </span>
          {i < WORKFLOW_STAGES.length - 1 && <span className="stage-flow__arrow">→</span>}
        </span>
      ))}
    </div>
  )
}
