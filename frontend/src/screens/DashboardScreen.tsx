import './DashboardScreen.css'
import type { ScreenId } from '../components/AppShell'
import { flattenAiRuns, flattenArtifacts, flattenValidations, type ProjectData } from '../hooks/useProjectData'
import { computeWorkflowStage } from '../hooks/workflowStage'
import { StageFlow } from './StageFlow'
import { TalpLanding } from './TalpLanding'

export function DashboardScreen({
  project,
  onNavigate,
}: {
  project: ProjectData | null
  onNavigate: (screen: ScreenId) => void
}) {
  if (!project) {
    return <TalpLanding onNavigate={onNavigate} />
  }

  return <DashboardProject project={project} />
}

function DashboardLanding({ onNavigate }: { onNavigate: (screen: ScreenId) => void }) {
  return (
    <div className="dashboard-landing">
      {/* Hero Section */}
      <div className="hero">
        <div className="hero__content">
          <div className="hero__badge">🚀 AI-Powered Engineering</div>
          <h1 className="hero__title">
            Transform Requirements
            <br />
            Into Production Code
          </h1>
          <p className="hero__subtitle">
            AI-assisted development where you stay in control. Get structured task breakdowns,
            intelligent recommendations, generated artifacts, and rigorous validation—all in one platform.
          </p>
          <button className="hero__cta" onClick={() => onNavigate('requirement')}>
            Start Building
          </button>
        </div>
        <div className="hero__visual">
          <div className="hero__icon">⚡</div>
        </div>
      </div>

      {/* Features Grid */}
      <section className="features">
        <h2 className="features__title">Why Engineering Teams Choose This</h2>
        <div className="features__grid">
          <Feature
            icon="🎯"
            title="Engineer-Led"
            description="You make every decision. AI assists, you approve. Full audit trail."
          />
          <Feature
            icon="🤖"
            title="AI-Powered"
            description="Analyze requirements, decompose tasks, generate code—all with AI help."
          />
          <Feature
            icon="✅"
            title="Validated"
            description="7-stage validation pipeline ensures every artifact meets quality standards."
          />
          <Feature
            icon="📊"
            title="Transparent"
            description="See exactly what AI generated, review all decisions, understand every step."
          />
        </div>
      </section>

      {/* Workflow Steps */}
      <section className="workflow">
        <h2 className="workflow__title">Your Workflow</h2>
        <div className="workflow__steps">
          <WorkflowStep
            step={1}
            title="Requirement"
            description="Define what you want to build—vague or detailed"
            icon="📝"
          />
          <div className="workflow__arrow">→</div>
          <WorkflowStep
            step={2}
            title="Analysis"
            description="AI identifies scope, ambiguities, constraints"
            icon="🔍"
          />
          <div className="workflow__arrow">→</div>
          <WorkflowStep
            step={3}
            title="Planning"
            description="Tasks with dependencies and success criteria"
            icon="📋"
          />
          <div className="workflow__arrow">→</div>
          <WorkflowStep
            step={4}
            title="Execute"
            description="Request AI assistance for each task"
            icon="⚙️"
          />
          <div className="workflow__arrow">→</div>
          <WorkflowStep
            step={5}
            title="Artifacts"
            description="AI generates code, tests, documentation"
            icon="📦"
          />
          <div className="workflow__arrow">→</div>
          <WorkflowStep
            step={6}
            title="Validate"
            description="Automated validation before approval"
            icon="✔️"
          />
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <h2>Ready to transform your requirements?</h2>
        <p>Select a project above or create a new one to get started</p>
        <button className="cta-button" onClick={() => onNavigate('requirement')}>
          Create New Project
        </button>
      </section>
    </div>
  )
}

function DashboardProject({ project }: { project: ProjectData }) {
  const { requirement, plan, artifactsByTaskId, validationsByArtifactId } = project
  const stage = computeWorkflowStage(project)

  const totalTasks = plan?.tasks.length ?? 0
  const approvedTasks = plan?.tasks.filter((t) => t.status === 'APPROVED').length ?? 0
  const aiRunCount = flattenAiRuns(plan).length
  const artifactCount = flattenArtifacts(plan, artifactsByTaskId).length
  const validations = flattenValidations(plan, artifactsByTaskId, validationsByArtifactId)
  const passed = validations.filter((v) => v.validation.status === 'PASSED').length
  const failed = validations.filter((v) => v.validation.status === 'FAILED').length
  const notValidated = validations.filter((v) => v.validation.status === 'NOT_VALIDATED').length

  return (
    <div className="project-dashboard">
      {/* Header */}
      <div className="project-header">
        <div className="project-header__content">
          <h1 className="project-header__id">{requirement.id}</h1>
          <p className="project-header__text">{requirement.text}</p>
        </div>
      </div>

      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-bar__stage">
          <span className="status-bar__label">Current Stage</span>
          <span className="status-bar__value">{stage.label}</span>
        </div>
        <div className="status-bar__flow">
          <StageFlow currentIndex={stage.index} />
        </div>
      </div>

      {/* Alerts */}
      {plan?.status === 'BLOCKED' && (
        <div className="alert alert--error">
          <span className="alert__icon">⚠️</span>
          <div>
            <div className="alert__title">Plan Blocked</div>
            <div className="alert__message">{plan.blocked_reason}</div>
          </div>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="metrics-section">
        <h2 className="metrics-section__title">Project Overview</h2>
        <div className="metrics-grid">
          <MetricCard
            label="Tasks"
            value={`${approvedTasks}/${totalTasks}`}
            status={approvedTasks === totalTasks ? 'complete' : 'progress'}
            icon="✓"
          />
          <MetricCard
            label="AI Runs"
            value={aiRunCount}
            status={aiRunCount > 0 ? 'active' : 'inactive'}
            icon="⚡"
          />
          <MetricCard
            label="Artifacts"
            value={artifactCount}
            status={artifactCount > 0 ? 'active' : 'inactive'}
            icon="📦"
          />
          <MetricCard
            label="Validations"
            value={`${passed}/${validations.length}`}
            status={failed === 0 && passed > 0 ? 'success' : failed > 0 ? 'warning' : 'neutral'}
            icon={failed === 0 ? '✓' : '⚠'}
          />
        </div>
      </div>

      {/* Quick Tips */}
      <div className="tips-box">
        <div className="tips-box__icon">💡</div>
        <div className="tips-box__content">
          <div className="tips-box__title">Next Step</div>
          <div className="tips-box__text">
            Follow the workflow: Requirement → Plan → Tasks → AI Runs → Artifacts → Validation → Final Report
          </div>
        </div>
      </div>
    </div>
  )
}

function Feature({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="feature-card">
      <div className="feature-card__icon">{icon}</div>
      <h3 className="feature-card__title">{title}</h3>
      <p className="feature-card__description">{description}</p>
    </div>
  )
}

function WorkflowStep({ step, title, description, icon }: { step: number; title: string; description: string; icon: string }) {
  return (
    <div className="workflow-item">
      <div className="workflow-item__number">{step}</div>
      <div className="workflow-item__icon">{icon}</div>
      <h4 className="workflow-item__title">{title}</h4>
      <p className="workflow-item__description">{description}</p>
    </div>
  )
}

function MetricCard({
  label,
  value,
  status,
  icon,
}: {
  label: string
  value: string | number
  status: string
  icon: string
}) {
  return (
    <div className={`metric-card metric-card--${status}`}>
      <div className="metric-card__icon">{icon}</div>
      <div className="metric-card__content">
        <div className="metric-card__value">{value}</div>
        <div className="metric-card__label">{label}</div>
      </div>
    </div>
  )
}
