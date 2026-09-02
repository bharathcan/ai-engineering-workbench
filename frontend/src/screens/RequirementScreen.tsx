import { useState, type ReactNode } from 'react'
import '../components/RequirementAnalyzer.css'
import '../components/AnalysisResult.css'
import {
  analyzeRequirement,
  clarifyRequirement,
  createRequirement,
  RequirementApiError,
  type RequirementAnalysisResult,
} from '../api/requirements'
import type { ProjectData } from '../hooks/useProjectData'
import type { ScreenId } from '../components/AppShell'

export function RequirementScreen({
  project,
  onRequirementCreated,
  onAnalyzed,
  onNavigate,
}: {
  project: ProjectData | null
  onRequirementCreated: (requirementId: string) => void
  onAnalyzed: () => void
  onNavigate?: (screen: ScreenId) => void
}) {
  const [text, setText] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const [working, setWorking] = useState(false)
  const [workError, setWorkError] = useState<string | null>(null)
  const [clarifications, setClarifications] = useState('')

  const handleCreate = async () => {
    setCreating(true)
    setCreateError(null)
    try {
      const created = await createRequirement(text)
      setText('')
      onRequirementCreated(created.id)
    } catch (err) {
      setCreateError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setCreating(false)
    }
  }

  const handleAnalyze = async () => {
    if (!project) return
    setWorking(true)
    setWorkError(null)
    try {
      await analyzeRequirement(project.requirement.id)
      onAnalyzed()
    } catch (err) {
      setWorkError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setWorking(false)
    }
  }

  const handleClarify = async () => {
    if (!project || clarifications.trim().length === 0) return
    setWorking(true)
    setWorkError(null)
    try {
      await clarifyRequirement(project.requirement.id, clarifications)
      setClarifications('')
      onAnalyzed()
    } catch (err) {
      setWorkError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setWorking(false)
    }
  }

  return (
    <section className="screen">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0 }}>Requirement</h2>
        {onNavigate && (
          <button
            type="button"
            onClick={() => onNavigate('dashboard')}
            style={{
              padding: '0.6rem 1.5rem',
              background: '#4b4dff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
          >
            ← Back to Dashboard
          </button>
        )}
      </div>

      <div className="screen-section">
        <h3>New Requirement</h3>
        <label htmlFor="requirement-input" className="analyzer__label">
          Requirement Input
        </label>
        <textarea
          id="requirement-input"
          className="analyzer__textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Build a scalable URL shortener service with APIs, persistence, and analytics."
          rows={4}
          disabled={creating}
        />
        <button
          type="button"
          className="analyzer__button"
          onClick={handleCreate}
          disabled={creating || text.trim().length === 0}
        >
          {creating ? 'Working…' : 'Create Requirement'}
        </button>
        {createError && <p className="analyzer__error">{createError}</p>}
      </div>

      {project && (
        <div className="screen-section">
          <h3>Selected Requirement — {project.requirement.id}</h3>
          <p>
            <strong>Original text:</strong> {project.requirement.text}
          </p>
          <p>
            <strong>Status:</strong> {project.requirement.status}
          </p>

          {!project.requirement.latest_analysis && (
            <button type="button" className="analyzer__button analyzer__button--primary" onClick={handleAnalyze} disabled={working}>
              {working ? 'Analyzing…' : 'Analyze Requirement'}
            </button>
          )}

          {project.requirement.latest_analysis && (
            <>
              <AnalysisResult result={project.requirement.latest_analysis} />

              {project.requirement.latest_analysis.ambiguities.some((a) => a.impact === 'HIGH') && (
                <div className="screen-section">
                  <h4>Resolve Ambiguities</h4>
                  <p>
                    One or more ambiguities above are HIGH impact, which blocks plan generation.
                    Answer them here — this amends {project.requirement.id} in place and
                    re-analyzes, rather than creating a new requirement.
                  </p>
                  <textarea
                    className="analyzer__textarea"
                    value={clarifications}
                    onChange={(e) => setClarifications(e.target.value)}
                    placeholder="e.g. AMB-001: track click count and referrer only. AMB-002: expect ~500 req/s."
                    rows={3}
                    disabled={working}
                  />
                  <button
                    type="button"
                    className="analyzer__button"
                    onClick={handleClarify}
                    disabled={working || clarifications.trim().length === 0}
                  >
                    {working ? 'Re-analyzing…' : 'Submit Clarification & Re-analyze'}
                  </button>
                </div>
              )}
            </>
          )}

          {workError && <p className="analyzer__error">{workError}</p>}
        </div>
      )}
    </section>
  )
}

function AnalysisResult({ result }: { result: RequirementAnalysisResult }) {
  return (
    <div className="analysis">
      <p className="badge badge--ai">AI-suggested analysis — not yet an engineering decision</p>

      <div className="analysis__summary">{result.summary}</div>

      <AnalysisSection title="Functional Requirements" count={result.functional_requirements.length}>
        <IdGrid items={result.functional_requirements} />
      </AnalysisSection>

      <AnalysisSection title="Non-Functional Requirements" count={result.non_functional_requirements.length}>
        <IdGrid items={result.non_functional_requirements} />
      </AnalysisSection>

      <AnalysisSection title="Ambiguities" count={result.ambiguities.length} tone="ambiguity">
        {result.ambiguities.length === 0 ? (
          <p className="analysis-empty">None identified.</p>
        ) : (
          <div className="detail-cards">
            {result.ambiguities.map((item) => (
              <div key={item.id} className="detail-card detail-card--ambiguity">
                <div className="detail-card__header">
                  <span className="detail-card__id">{item.id}</span>
                  <span className={`impact-pill impact-pill--${item.impact.toLowerCase()}`}>
                    {item.impact}
                  </span>
                </div>
                <p className="detail-card__description">{item.description}</p>
                <p className="detail-card__meta">
                  <strong>Why it matters:</strong> {item.why_it_matters}
                </p>
                <p className="detail-card__meta">
                  <strong>Information needed:</strong> {item.information_needed}
                </p>
              </div>
            ))}
          </div>
        )}
      </AnalysisSection>

      <AnalysisSection title="Assumptions" count={result.assumptions.length} tone="assumption">
        {result.assumptions.length === 0 ? (
          <p className="analysis-empty">None made.</p>
        ) : (
          <div className="detail-cards">
            {result.assumptions.map((item) => (
              <div key={item.id} className="detail-card detail-card--assumption">
                <div className="detail-card__header">
                  <span className="detail-card__id">{item.id}</span>
                </div>
                <p className="detail-card__description">{item.description}</p>
                <p className="detail-card__meta">
                  <strong>Reason:</strong> {item.reason}
                </p>
                <p className="detail-card__meta">
                  <strong>Impact if wrong:</strong> {item.impact}
                </p>
              </div>
            ))}
          </div>
        )}
      </AnalysisSection>

      <AnalysisSection title="Constraints" count={result.constraints.length}>
        <IdGrid items={result.constraints} />
      </AnalysisSection>

      <AnalysisSection title="Success Criteria" count={result.success_criteria.length} tone="success">
        <IdGrid items={result.success_criteria} />
      </AnalysisSection>

      <AnalysisSection title="Engineering Concerns" count={result.engineering_concerns.length} tone="engineering">
        <IdGrid items={result.engineering_concerns} />
      </AnalysisSection>
    </div>
  )
}

function AnalysisSection({
  title,
  count,
  tone,
  children,
}: {
  title: string
  count: number
  tone?: 'ambiguity' | 'assumption' | 'success' | 'engineering'
  children: ReactNode
}) {
  return (
    <div className={`analysis-section${tone ? ` analysis-section--${tone}` : ''}`}>
      <div className="analysis-section__header">
        <span className="analysis-section__title">{title}</span>
        <span className="analysis-section__count">{count}</span>
      </div>
      {children}
    </div>
  )
}

function IdGrid({ items }: { items: { id: string; description: string }[] }) {
  if (items.length === 0) {
    return <p className="analysis-empty">None identified.</p>
  }
  return (
    <div className="id-grid">
      {items.map((item) => (
        <div key={item.id} className="id-card">
          <span className="id-card__id">{item.id}</span>
          <span>{item.description}</span>
        </div>
      ))}
    </div>
  )
}
