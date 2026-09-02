import type { Artifact } from '../api/artifacts'
import type { RequirementAnalysisResult, RequirementResponse } from '../api/requirements'
import type { AIRun, EngineeringPlan, EngineeringTask } from '../api/tasks'
import type { Validation } from '../api/validations'
import type { ProjectData } from '../hooks/useProjectData'

export const analysisFixture: RequirementAnalysisResult = {
  summary: 'A URL shortener with APIs, persistence, and analytics.',
  functional_requirements: [{ id: 'FR-001', description: 'Shorten a long URL.' }],
  non_functional_requirements: [{ id: 'NFR-001', description: 'Must scale to high traffic.' }],
  ambiguities: [
    {
      id: 'AMB-001',
      description: 'Custom alias length is unspecified.',
      why_it_matters: 'Affects schema constraints.',
      impact: 'MEDIUM',
      information_needed: 'A max length for custom aliases.',
    },
  ],
  assumptions: [
    { id: 'ASM-001', description: 'Short codes are case-sensitive.', reason: 'Base62 default.', impact: 'Low if wrong.' },
  ],
  constraints: [{ id: 'CON-001', description: 'Must not require paid infrastructure.' }],
  success_criteria: [{ id: 'SC-001', description: 'Redirects resolve in under 50ms.' }],
  engineering_concerns: [{ id: 'ENG-001', description: 'Collision handling under load.' }],
}

export const requirementFixture: RequirementResponse = {
  id: 'REQ-001',
  text: 'Build a scalable URL shortener service with APIs, persistence, and analytics.',
  status: 'ANALYZED',
  created_at: '2026-01-01T00:00:00Z',
  latest_analysis: analysisFixture,
}

export const decisionFixture = {
  id: 'DEC-001',
  ai_run_id: null,
  decision: 'ACCEPT' as const,
  rationale: 'Looks correct.',
  changes: null,
  reviewer: null,
  created_at: '2026-01-01T00:05:00Z',
}

export const aiRunFixture: AIRun = {
  id: 'RUN-001',
  task_id: 'TASK-001',
  provider: 'anthropic',
  model: 'claude-test',
  assistance_type: 'CODE_GENERATION',
  instructions: null,
  prompt: 'Generate the short-code service.',
  status: 'COMPLETED',
  response: {
    summary: 'Implement Base62 short-code generation.',
    approach: 'Use a CSPRNG and retry on collision.',
    files_to_change: ['app/services/url_service.py'],
    proposed_changes: ['Add create_short_url()'],
    tests_to_add: ['test_url_service.py'],
    risks: ['Collision under extreme load.'],
    assumptions: ['Base62 alphabet is fixed.'],
    confidence: 'HIGH',
  },
  error: null,
  duration_ms: 120,
  revised_from_ai_run_id: null,
  decisions: [decisionFixture],
  created_at: '2026-01-01T00:02:00Z',
}

export const taskFixture: EngineeringTask = {
  id: 'TASK-001',
  plan_id: 'PLAN-001',
  title: 'Implement short-code generation',
  description: 'Generate a unique Base62 short code for each submitted URL.',
  type: 'BACKEND',
  requirement_refs: ['FR-001'],
  dependencies: [],
  sequence: 1,
  acceptance_criteria: ['Short codes are unique.', 'Collisions are retried, not pre-checked.'],
  ai_assistance_type: 'CODE_GENERATION',
  risks: [{ id: 'RISK-001', description: 'High collision rate under load.', impact: 'LOW' }],
  status: 'REVIEW_REQUIRED',
  review_status: 'PENDING',
  decisions: [],
  ai_runs: [],
  created_at: '2026-01-01T00:01:00Z',
}

export const approvedTaskFixture: EngineeringTask = {
  ...taskFixture,
  id: 'TASK-002',
  title: 'Implement redirect endpoint',
  sequence: 2,
  status: 'APPROVED',
  review_status: 'ACCEPT',
  decisions: [decisionFixture],
  ai_runs: [aiRunFixture],
}

export const planFixture: EngineeringPlan = {
  id: 'PLAN-001',
  requirement_id: 'REQ-001',
  requirement_analysis_id: 'ANALYSIS-001',
  status: 'GENERATED',
  blocked_reason: null,
  summary: 'Decomposed into short-code generation, redirect, and analytics tasks.',
  tasks: [taskFixture, approvedTaskFixture],
  assumptions: ['Base62 alphabet is fixed.'],
  unresolved_ambiguities: [],
  risks: [{ id: 'RISK-002', description: 'No rate limiting yet.', impact: 'MEDIUM' }],
  review_status: 'DRAFT',
  created_at: '2026-01-01T00:01:30Z',
}

export const artifactFixture: Artifact = {
  id: 'ART-001',
  task_id: 'TASK-002',
  ai_run_id: 'RUN-001',
  artifact_type: 'SOURCE_CODE',
  path: 'backend/app/services/url_service.py',
  content: 'def create_short_url():\n    ...',
  description: 'Short-code generation service.',
  status: 'PENDING_REVIEW',
  version: 1,
  supersedes_artifact_id: null,
  diff: null,
  decisions: [],
  created_at: '2026-01-01T00:03:00Z',
}

export const passedValidationFixture: Validation = {
  id: 'VAL-001',
  artifact_id: 'ART-001',
  task_id: 'TASK-002',
  validation_type: 'UNIT_TEST',
  command: 'pytest tests/test_url_service.py',
  status: 'PASSED',
  output: '5 passed in 0.42s',
  evidence: '5 passed in 0.42s',
  error: null,
  duration_ms: 420,
  metadata: {},
  created_at: '2026-01-01T00:04:00Z',
}

export const notValidatedFixture: Validation = {
  id: 'VAL-002',
  artifact_id: 'ART-001',
  task_id: 'TASK-002',
  validation_type: 'SECURITY',
  command: '',
  status: 'NOT_VALIDATED',
  output: '',
  evidence: 'No security scan has been run for this artifact.',
  error: null,
  duration_ms: 0,
  metadata: {},
  created_at: '2026-01-01T00:04:30Z',
}

export const fullProjectFixture: ProjectData = {
  requirement: requirementFixture,
  plan: planFixture,
  artifactsByTaskId: { 'TASK-002': [artifactFixture] },
  validationsByArtifactId: { 'ART-001': [passedValidationFixture, notValidatedFixture] },
}
