import { useState, type ReactNode } from 'react'
import './RequirementAnalyzer.css'
import {
  analyzeRequirement,
  createRequirement,
  RequirementApiError,
  type RequirementAnalysisResult,
} from '../api/requirements'
import { EngineeringPlanPanel } from './EngineeringPlanPanel'

type AnalyzerState =
  | { phase: 'idle' }
  | { phase: 'analyzing' }
  | { phase: 'done'; requirementId: string; result: RequirementAnalysisResult }
  | { phase: 'error'; message: string }

export function RequirementAnalyzer() {
  const [text, setText] = useState('')
  const [state, setState] = useState<AnalyzerState>({ phase: 'idle' })

  const handleAnalyze = async () => {
    setState({ phase: 'analyzing' })
    try {
      const created = await createRequirement(text)
      const analyzed = await analyzeRequirement(created.id)
      if (!analyzed.latest_analysis) {
        setState({ phase: 'error', message: 'Analysis completed with no result.' })
        return
      }
      setState({ phase: 'done', requirementId: created.id, result: analyzed.latest_analysis })
    } catch (err) {
      const message = err instanceof RequirementApiError ? err.message : 'Something went wrong.'
      setState({ phase: 'error', message })
    }
  }

  const isAnalyzing = state.phase === 'analyzing'

  return (
    <section className="analyzer">
      <h2>Requirement Analyzer</h2>

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
        disabled={isAnalyzing}
      />

      <button
        type="button"
        className="analyzer__button"
        onClick={handleAnalyze}
        disabled={isAnalyzing || text.trim().length === 0}
      >
        {isAnalyzing ? 'Analyzing…' : 'Analyze Requirement'}
      </button>

      {state.phase === 'error' && <p className="analyzer__error">{state.message}</p>}

      {state.phase === 'done' && (
        <>
          <AnalysisResult result={state.result} />
          <EngineeringPlanPanel requirementId={state.requirementId} />
        </>
      )}
    </section>
  )
}

function AnalysisResult({ result }: { result: RequirementAnalysisResult }) {
  return (
    <div className="analysis-result">
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
      <h3>{title}</h3>
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
