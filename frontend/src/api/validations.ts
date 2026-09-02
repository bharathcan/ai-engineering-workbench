import { RequirementApiError } from './requirements'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type ValidationType =
  | 'UNIT_TEST'
  | 'INTEGRATION_TEST'
  | 'API_CONTRACT'
  | 'STATIC_ANALYSIS'
  | 'SECURITY'
  | 'PERFORMANCE'
  | 'BUILD'

export interface Validation {
  id: string
  artifact_id: string
  task_id: string
  validation_type: ValidationType
  command: string
  status: 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED' | 'NOT_VALIDATED'
  output: string
  evidence: string
  error: string | null
  duration_ms: number
  metadata: Record<string, unknown>
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

export async function validateArtifact(
  artifactId: string,
  validationType: ValidationType,
): Promise<Validation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/artifacts/${artifactId}/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ validation_type: validationType }),
  })
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function getArtifactValidations(artifactId: string): Promise<Validation[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/artifacts/${artifactId}/validations`)
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}
