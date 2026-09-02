import { RequirementApiError } from './requirements'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export interface RiskItem {
  id: string
  description: string
  impact: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface EngineerDecision {
  id: string
  ai_run_id: string | null
  decision: 'ACCEPT' | 'MODIFY' | 'REJECT'
  rationale: string | null
  changes: string | null
  reviewer: string | null
  created_at: string
}

export type AIAssistRequestType =
  | 'DESIGN'
  | 'CODE_GENERATION'
  | 'DEBUGGING'
  | 'REFACTORING'
  | 'TEST_GENERATION'
  | 'DOCUMENTATION'
  | 'SECURITY_REVIEW'
  | 'PERFORMANCE_REVIEW'

export interface AIRecommendation {
  summary: string
  approach: string
  files_to_change: string[]
  proposed_changes: string[]
  tests_to_add: string[]
  risks: string[]
  assumptions: string[]
  confidence: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface AIRun {
  id: string
  task_id: string
  provider: string
  model: string
  assistance_type: AIAssistRequestType
  instructions: string | null
  prompt: string
  status: 'COMPLETED' | 'FAILED'
  response: AIRecommendation | null
  error: string | null
  duration_ms: number
  revised_from_ai_run_id: string | null
  decisions: EngineerDecision[]
  created_at: string
}

export interface EngineeringTask {
  id: string
  plan_id: string
  title: string
  description: string
  type: string
  requirement_refs: string[]
  dependencies: string[]
  sequence: number
  acceptance_criteria: string[]
  ai_assistance_type: string
  risks: RiskItem[]
  status: string
  review_status: string
  decisions: EngineerDecision[]
  ai_runs: AIRun[]
  created_at: string
}

export interface EngineeringPlan {
  id: string
  requirement_id: string
  requirement_analysis_id: string
  status: 'GENERATED' | 'BLOCKED'
  blocked_reason: string | null
  summary: string
  tasks: EngineeringTask[]
  assumptions: string[]
  unresolved_ambiguities: string[]
  risks: RiskItem[]
  review_status: string
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

export async function generatePlan(requirementId: string): Promise<EngineeringPlan> {
  const response = await fetch(`${API_BASE_URL}/api/v1/engineering-plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ requirement_id: requirementId }),
  })
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function getPlan(requirementId: string): Promise<EngineeringPlan> {
  const response = await fetch(`${API_BASE_URL}/api/v1/engineering-plans/${requirementId}`)
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function decideTask(
  taskId: string,
  decision: 'ACCEPT' | 'MODIFY' | 'REJECT',
  rationale?: string,
  changes?: string,
): Promise<EngineeringTask> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, rationale, changes }),
  })
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function getTask(taskId: string): Promise<EngineeringTask> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}`)
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function requestAiAssist(
  taskId: string,
  assistanceType: AIAssistRequestType,
  instructions?: string,
): Promise<AIRun> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}/ai-assist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ assistance_type: assistanceType, instructions }),
  })
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}

export async function decideAiRun(
  aiRunId: string,
  decision: 'ACCEPT' | 'MODIFY' | 'REJECT',
  rationale?: string,
  changes?: string,
): Promise<AIRun> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai-runs/${aiRunId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, rationale, changes }),
  })
  if (!response.ok) {
    throw new RequirementApiError(await parseErrorDetail(response), response.status)
  }
  return response.json()
}
