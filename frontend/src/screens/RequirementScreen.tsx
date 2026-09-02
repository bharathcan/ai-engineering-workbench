import { useState, type ReactNode } from 'react'
import '../components/RequirementAnalyzer.css'
import {
  analyzeRequirement,
  createRequirement,
  RequirementApiError,
  type RequirementAnalysisResult,
} from '../api/requirements'
import type { ProjectData } from '../hooks/useProjectData'

export function RequirementScreen({
  project,
  onRequirementCreated,
  onAnalyzed,
}: {
  project: ProjectData | null
  onRequirementCreated: (requirementId: string) => void
  onAnalyzed: () => void
}) {
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const created = await createRequirement(text)
      setText('')
      onRequirementCreated(created.id)
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleAnalyze = async () => {
    if (!project) return
    setSubmitting(true)
    setError(null)
    try {
      await analyzeRequirement(project.requirement.id)
      onAnalyzed()
    } catch (err) {
      setError(err instanceof RequirementApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="screen">
      <h2>Requirement</h2>

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
          disabled={submitting}
        />
        <button
          type="button"
          className="analyzer__button"
          onClick={handleCreate}
          disabled={submitting || text.trim().length === 0}
        >
          {submitting ? 'Working…' : 'Create Requirement'}
        </button>
        {error && <p className="analyzer__error">{error}</p>}
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
            <button type="button" onClick={handleAnalyze} disabled={submitting}>
              {submitting ? 'Analyzing…' : 'Analyze Requirement'}
            </button>
          )}

          {project.requirement.latest_analysis && (
            <AnalysisResult result={project.requirement.latest_analysis} />
          )}
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
