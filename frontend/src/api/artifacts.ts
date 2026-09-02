import { RequirementApiError } from './requirements'
import type { EngineerDecision } from './tasks'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type ArtifactType =
  | 'SOURCE_CODE'
  | 'API_CONTRACT'
  | 'DATABASE_SCHEMA'
  | 'TEST'
  | 'DOCUMENTATION'
  | 'CONFIGURATION'
  | 'ARCHITECTURE'

export interface Artifact {
  id: string
  task_id: string
  ai_run_id: string
  artifact_type: ArtifactType
  path: string
  content: string
  description: string
  status: 'PENDING_REVIEW' | 'APPROVED' | 'NEEDS_REVISION' | 'REJECTED'
  version: number
  supersedes_artifact_id: string | null
  diff: string | null
  decisions: EngineerDecision[]
  created_at: string
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    return `Request failed with status ${response.status}`
  } catch {
    return `Request failed with status ${response.status}`
  }
}

export async function generateArtifacts(aiRunId: string): Promise<Artifact[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai-runs/${aiRunId}/artifacts`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function getTaskArtifacts(taskId: string): Promise<Artifact[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}/artifacts`)
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function decideArtifact(
  artifactId: string,
  decision: 'ACCEPT' | 'MODIFY' | 'REJECT',
  rationale?: string,
  changes?: string,
): Promise<Artifact> {
  const response = await fetch(`${API_BASE_URL}/api/v1/artifacts/${artifactId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, rationale, changes }),
  })
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}
