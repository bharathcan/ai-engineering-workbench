import type { ProjectData } from './useProjectData'

export const WORKFLOW_STAGES = [
  'Requirement',
  'Plan',
  'Execute',
  'Review',
  'Artifacts',
  'Validate',
  'Report',
] as const

export type WorkflowStage = (typeof WORKFLOW_STAGES)[number]

/** There is no explicit "stage" field on the backend — a project's stage is
 * inferred client-side from what data exists so far. This is a heuristic for
 * display purposes only, not a persisted or authoritative value. */
export function computeWorkflowStage(data: ProjectData | null): {
  label: WorkflowStage | 'Blocked'
  index: number
} {
  if (!data) return { label: 'Requirement', index: 0 }
  if (!data.requirement.latest_analysis) return { label: 'Requirement', index: 0 }
  if (!data.plan) return { label: 'Plan', index: 1 }
  if (data.plan.status === 'BLOCKED') return { label: 'Blocked', index: 1 }

  const tasks = data.plan.tasks
  const anyAiRuns = tasks.some((t) => t.ai_runs.length > 0)
  if (!anyAiRuns) return { label: 'Execute', index: 2 }

  const anyPendingAiRunReview = tasks.some((t) =>
    t.ai_runs.some((r) => r.status === 'COMPLETED' && r.decisions.length === 0),
  )
  if (anyPendingAiRunReview) return { label: 'Review', index: 3 }

  const artifactCount = Object.values(data.artifactsByTaskId).flat().length
  if (artifactCount === 0) return { label: 'Artifacts', index: 4 }

  const validationCount = Object.values(data.validationsByArtifactId).flat().length
  if (validationCount === 0) return { label: 'Validate', index: 5 }

  return { label: 'Report', index: 6 }
}
