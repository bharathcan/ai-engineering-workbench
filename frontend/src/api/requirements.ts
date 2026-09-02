const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export interface FunctionalRequirementItem {
  id: string
  description: string
}

export interface NonFunctionalRequirementItem {
  id: string
  description: string
}

export interface AmbiguityItem {
  id: string
  description: string
  why_it_matters: string
  impact: 'LOW' | 'MEDIUM' | 'HIGH'
  information_needed: string
}

export interface AssumptionItem {
  id: string
  description: string
  reason: string
  impact: string
}

export interface ConstraintItem {
  id: string
  description: string
}

export interface SuccessCriterionItem {
  id: string
  description: string
}

export interface EngineeringConcernItem {
  id: string
  description: string
}

export interface RequirementAnalysisResult {
  summary: string
  functional_requirements: FunctionalRequirementItem[]
  non_functional_requirements: NonFunctionalRequirementItem[]
  ambiguities: AmbiguityItem[]
  assumptions: AssumptionItem[]
  constraints: ConstraintItem[]
  success_criteria: SuccessCriterionItem[]
  engineering_concerns: EngineeringConcernItem[]
}

export interface RequirementResponse {
  id: string
  text: string
  status: string
  created_at: string
  latest_analysis: RequirementAnalysisResult | null
}

export class RequirementApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
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

export async function createRequirement(text: string): Promise<RequirementResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/requirements`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function analyzeRequirement(requirementId: string): Promise<RequirementResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/requirements/${requirementId}/analyze`,
    { method: 'POST' },
  )
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function getRequirement(requirementId: string): Promise<RequirementResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/requirements/${requirementId}`)
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function listRequirements(): Promise<RequirementResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/requirements`)
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}
