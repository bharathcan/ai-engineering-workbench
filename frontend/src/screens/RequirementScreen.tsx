import { useState, type ReactNode } from 'react'
import '../components/RequirementAnalyzer.css'
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
    <div className="analysis-result">
      <p className="badge badge--ai">AI-suggested analysis — not yet an engineering decision</p>

      <ResultBlock title="Summary">
        <p>{result.summary}</p>
      </ResultBlock>

      <ResultBlock title="Functional Requirements">
        <IdList items={result.functional_requirements} />
      </ResultBlock>

      <ResultBlock title="Non-Functional Requirements">
        <IdList items={result.non_functional_requirements} />
      </ResultBlock>

      <ResultBlock title="Ambiguities" tone="ambiguity">
        {result.ambiguities.length === 0 ? (
          <p className="analysis-result__empty">None identified.</p>
        ) : (
          <ul className="analysis-result__list">
            {result.ambiguities.map((item) => (
              <li key={item.id} className="analysis-result__card analysis-result__card--ambiguity">
                <div className="analysis-result__card-header">
                  <strong>{item.id}</strong>
                  <span className={`impact-badge impact-badge--${item.impact.toLowerCase()}`}>
                    {item.impact}
                  </span>
                </div>
                <p>{item.description}</p>
                <p className="analysis-result__meta">
                  <strong>Why it matters:</strong> {item.why_it_matters}
                </p>
                <p className="analysis-result__meta">
                  <strong>Information needed:</strong> {item.information_needed}
                </p>
              </li>
            ))}
          </ul>
        )}
      </ResultBlock>

      <ResultBlock title="Assumptions" tone="assumption">
        {result.assumptions.length === 0 ? (
          <p className="analysis-result__empty">None made.</p>
        ) : (
          <ul className="analysis-result__list">
            {result.assumptions.map((item) => (
              <li key={item.id} className="analysis-result__card analysis-result__card--assumption">
                <strong>{item.id}</strong>
                <p>{item.description}</p>
                <p className="analysis-result__meta">
                  <strong>Reason:</strong> {item.reason}
                </p>
                <p className="analysis-result__meta">
                  <strong>Impact if wrong:</strong> {item.impact}
                </p>
              </li>
            ))}
          </ul>
        )}
      </ResultBlock>

      <ResultBlock title="Constraints">
        <IdList items={result.constraints} />
      </ResultBlock>

      <ResultBlock title="Success Criteria">
        <IdList items={result.success_criteria} />
      </ResultBlock>

      <ResultBlock title="Engineering Concerns">
        <IdList items={result.engineering_concerns} />
      </ResultBlock>
    </div>
  )
}

function ResultBlock({
  title,
  tone,
  children,
}: {
  title: string
  tone?: 'ambiguity' | 'assumption'
  children: ReactNode
}) {
  return (
    <div className={`result-block${tone ? ` result-block--${tone}` : ''}`}>
      <h4>{title}</h4>
      {children}
    </div>
  )
}

function IdList({ items }: { items: { id: string; description: string }[] }) {
  if (items.length === 0) {
    return <p className="analysis-result__empty">None identified.</p>
  }
  return (
    <ul className="analysis-result__list">
      {items.map((item) => (
        <li key={item.id} className="analysis-result__card">
          <strong>{item.id}</strong> — {item.description}
        </li>
      ))}
    </ul>
  )
}
