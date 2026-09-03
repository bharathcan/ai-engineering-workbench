import { useCallback, useEffect, useState } from 'react'
import type { Artifact } from '../api/artifacts'
import { getTaskArtifacts } from '../api/artifacts'
import { RequirementApiError, getRequirement, type RequirementResponse } from '../api/requirements'
import { getPlan, type AIRun, type EngineeringPlan, type EngineeringTask } from '../api/tasks'
import { getArtifactValidations, type Validation } from '../api/validations'

/** A "project" in this UI is one Requirement and everything traceable back
 * to it: its analysis, its engineering plan and tasks, each task's AI
 * runs (already embedded in the task response), each task's artifacts,
 * and each artifact's validations. This hook assembles all of it once so
 * every Phase 11 screen reads from one consistent snapshot instead of
 * re-fetching and potentially disagreeing with each other. */
export interface ProjectData {
  requirement: RequirementResponse
  plan: EngineeringPlan | null
  artifactsByTaskId: Record<string, Artifact[]>
  validationsByArtifactId: Record<string, Validation[]>
}

export function flattenAiRuns(plan: EngineeringPlan | null): { task: EngineeringTask; run: AIRun }[] {
  if (!plan) return []
  return plan.tasks.flatMap((task) => task.ai_runs.map((run) => ({ task, run })))
}

export function flattenArtifacts(
  plan: EngineeringPlan | null,
  artifactsByTaskId: Record<string, Artifact[]>,
): { task: EngineeringTask; artifact: Artifact }[] {
  if (!plan) return []
  return plan.tasks.flatMap((task) =>
    (artifactsByTaskId[task.id] ?? []).map((artifact) => ({ task, artifact })),
  )
}

export function flattenValidations(
  plan: EngineeringPlan | null,
  artifactsByTaskId: Record<string, Artifact[]>,
  validationsByArtifactId: Record<string, Validation[]>,
): { task: EngineeringTask; artifact: Artifact; validation: Validation }[] {
  return flattenArtifacts(plan, artifactsByTaskId).flatMap(({ task, artifact }) =>
    (validationsByArtifactId[artifact.id] ?? []).map((validation) => ({
      task,
      artifact,
      validation,
    })),
  )
}

export function useProjectData(requirementId: string | null) {
  const [data, setData] = useState<ProjectData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    if (!requirementId) {
      setData(null)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const requirement = await getRequirement(requirementId)

      let plan: EngineeringPlan | null = null
      try {
        plan = await getPlan(requirementId)
      } catch (err) {
        // 404 just means no plan has been generated yet — not an error
        // state for the project as a whole.
        if (!(err instanceof RequirementApiError && err.status === 404)) throw err
      }

      const artifactsByTaskId: Record<string, Artifact[]> = {}
      const validationsByArtifactId: Record<string, Validation[]> = {}
      if (plan && plan.status === 'GENERATED') {
        // Fetch every task's artifacts concurrently rather than one at a
        // time — with N tasks this was N sequential round trips before.
        const perTaskArtifacts = await Promise.all(
          plan.tasks.map((task) => getTaskArtifacts(task.id)),
        )
        plan.tasks.forEach((task, i) => {
          artifactsByTaskId[task.id] = perTaskArtifacts[i]
        })

        // Same fix for validations, one level down: every artifact across
        // every task, fetched concurrently instead of nested sequential
        // awaits (that was the real bottleneck once any task accumulated
        // more than a handful of artifacts).
        const allArtifacts = perTaskArtifacts.flat()
        const perArtifactValidations = await Promise.all(
          allArtifacts.map((artifact) => getArtifactValidations(artifact.id)),
        )
        allArtifacts.forEach((artifact, i) => {
          validationsByArtifactId[artifact.id] = perArtifactValidations[i]
        })
      }

      setData({ requirement, plan, artifactsByTaskId, validationsByArtifactId })
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [requirementId])

  useEffect(() => {
    reload()
  }, [reload])

  return { data, loading, error, reload }
}
