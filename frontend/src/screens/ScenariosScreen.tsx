import { useState } from 'react'
import { analyzeRequirement, createRequirement, RequirementApiError } from '../api/requirements'
import { generatePlan, type EngineeringPlan } from '../api/tasks'
import type { ScreenId } from '../components/AppShell'
import '../components/EngineeringPlanPanel.css'
import type { ProjectData } from '../hooks/useProjectData'

const AMBIGUOUS_TEXT = 'Improve the analytics.'

type Tab = 'greenfield' | 'brownfield' | 'ambiguous'

type DemoState =
  | { phase: 'idle' }
  | { phase: 'running' }
  | { phase: 'blocked'; requirementId: string; plan: EngineeringPlan }
  | { phase: 'unexpectedly-not-blocked'; requirementId: string; plan: EngineeringPlan }
  | { phase: 'error'; message: string }

const INTERPRETATIONS = [
  {
    id: 'A',
    title: 'Reporting Analytics',
    scope: 'Scheduled/aggregate reports — daily and weekly click summaries, top-performing links.',
    pros: ['Low implementation complexity', 'Low privacy risk — aggregates only'],
    cons: ['Not real-time', 'No per-visitor or behavioral insight'],
  },
  {
    id: 'B',
    title: 'Real-Time Analytics',
    scope: 'Live dashboards / streaming click counts as they happen.',
    pros: ['Immediate visibility into traffic'],
    cons: [
      'Requires more infrastructure (polling or streaming transport)',
      'No deeper insight into who is clicking, only how many, in real time',
    ],
  },
  {
    id: 'C',
    title: 'Advanced User Analytics',
    scope: 'Device, browser, referrer, geographic, and repeat-visitor tracking per click.',
    pros: ['Richest insight into how links are actually being used'],
    cons: ['Additional data collection, privacy/security implications, increased complexity'],
    chosen: true,
  },
]

export function ScenariosScreen({
  project,
  onRequirementCreated,
  onNavigate,
}: {
  project: ProjectData | null
  onRequirementCreated: (requirementId: string) => void
  onNavigate: (screen: ScreenId) => void
}) {
  const [tab, setTab] = useState<Tab>('greenfield')

  return (
    <section className="screen">
      <h2>Scenarios</h2>
      <div className="tabs">
        <button
          type="button"
          className={'tabs__item' + (tab === 'greenfield' ? ' tabs__item--active' : '')}
          onClick={() => setTab('greenfield')}
        >
          Greenfield
        </button>
        <button
          type="button"
          className={'tabs__item' + (tab === 'brownfield' ? ' tabs__item--active' : '')}
          onClick={() => setTab('brownfield')}
        >
          Brownfield
        </button>
        <button
          type="button"
          className={'tabs__item' + (tab === 'ambiguous' ? ' tabs__item--active' : '')}
          onClick={() => setTab('ambiguous')}
        >
          Ambiguous
        </button>
      </div>

      {tab === 'greenfield' && <GreenfieldTab project={project} onNavigate={onNavigate} />}
      {tab === 'brownfield' && <BrownfieldTab />}
      {tab === 'ambiguous' && (
        <AmbiguousTab onRequirementCreated={onRequirementCreated} onNavigate={onNavigate} />
      )}
    </section>
  )
}

function GreenfieldTab({
  project,
  onNavigate,
}: {
  project: ProjectData | null
  onNavigate: (screen: ScreenId) => void
}) {
  return (
    <div>
      <h3>Greenfield — Build a scalable URL shortener service with APIs, persistence, and analytics</h3>
      <p>
        This is the mandatory use case for the whole workbench, built from a blank codebase across
        Phases 6–10: short-code generation, redirect, persistence, and analytics, all produced
        through the same Requirement → Plan → AI Run → Engineer Decision → Artifact → Validation
        pipeline used everywhere else in this UI.
      </p>
      <p>
        Select the URL shortener requirement from the project selector at the top of the page, then
        use the Dashboard, Engineering Plan, Tasks, AI Runs, Artifacts, and Validation screens to
        walk through exactly how it was built — this is not a separate simulated view, it is the
        real recorded history.
      </p>
      {project && (
        <button type="button" onClick={() => onNavigate('dashboard')}>
          View selected project's Dashboard
        </button>
      )}
    </div>
  )
}

function BrownfieldTab() {
  return (
    <div>
      <h3>Brownfield — Existing URL shortener with slow redirects</h3>
      <p>
        <strong>Requirement:</strong> "The existing URL shortener has slow redirect performance.
        Improve performance without changing the public API."
      </p>
      <p>
        Unlike the Greenfield case, this scenario runs the workbench against an{' '}
        <em>already-built</em> system (the Phase 8 URL shortener) instead of starting from nothing.
        The Requirement Analyzer flagged that "slow" was never quantified — no baseline or target
        was given — which had to be resolved by measuring the real system before proposing a fix,
        not by assuming a number.
      </p>
      <ul>
        <li>
          <strong>Baseline measured:</strong> p50 0.981&nbsp;ms, p95 1.185&nbsp;ms, throughput
          990.4&nbsp;req/s (500 sequential requests, real `uvicorn` instance).
        </li>
        <li>
          <strong>AI recommendation:</strong> defer the click-count write to a background task so
          the redirect response doesn't wait on it.
        </li>
        <li>
          <strong>Engineer review:</strong> MODIFY — required an explicit regression test pinning
          the exact response contract before accepting "unchanged public API" as verified.
        </li>
        <li>
          <strong>Real regression found during validation, not hidden:</strong> deferring the write
          introduced a lost-update race (498/500 clicks recorded instead of 500/500). Root cause
          was a Python-side read-modify-write; fixed with a single atomic SQL{' '}
          <code>UPDATE ... SET click_count = click_count + 1</code>.
        </li>
        <li>
          <strong>Result:</strong> ~33% p50 improvement, ~34% p95 improvement, ~44% throughput
          improvement, click accuracy restored to 500/500, public API contract unchanged (verified
          by a dedicated test).
        </li>
      </ul>
      <p>
        Full write-up with both "before" and "after" (including the race, reported rather than
        discarded) is in the root <code>README.md</code> (Demonstration Scenarios), with the
        durable, re-runnable proof in <code>backend/tests/test_brownfield_performance_flow.py</code>.
      </p>
    </div>
  )
}

function AmbiguousTab({
  onRequirementCreated,
  onNavigate,
}: {
  onRequirementCreated: (requirementId: string) => void
  onNavigate: (screen: ScreenId) => void
}) {
  const [demo, setDemo] = useState<DemoState>({ phase: 'idle' })

  const runLiveDemo = async () => {
    setDemo({ phase: 'running' })
    try {
      const created = await createRequirement(AMBIGUOUS_TEXT)
      await analyzeRequirement(created.id)
      const plan = await generatePlan(created.id)
      if (plan.status === 'BLOCKED') {
        setDemo({ phase: 'blocked', requirementId: created.id, plan })
      } else {
        setDemo({ phase: 'unexpectedly-not-blocked', requirementId: created.id, plan })
      }
    } catch (err) {
      setDemo({
        phase: 'error',
        message: err instanceof RequirementApiError ? err.message : 'Something went wrong.',
      })
    }
  }

  return (
    <div>
      <h3>Ambiguous — "Improve the analytics."</h3>
      <p>
        This requirement is deliberately underspecified. The workbench must not guess what
        "improve" means — it must stop and require an explicit engineer decision. This tab does
        not implement anything automatically.
      </p>

      <button type="button" onClick={runLiveDemo} disabled={demo.phase === 'running'}>
        {demo.phase === 'running'
          ? 'Submitting…'
          : 'Submit "Improve the analytics." and observe the live gate'}
      </button>

      {demo.phase === 'error' && <p className="task-card__error">{demo.message}</p>}

      {demo.phase === 'blocked' && (
        <div className="plan-panel__blocked" style={{ marginTop: '1rem' }}>
          <h4>BLOCKED — ENGINEER INPUT REQUIRED</h4>
          <p>
            <strong>Reason:</strong> {demo.plan.blocked_reason}
          </p>
          <p>
            Requirement <code>{demo.requirementId}</code> was created and analyzed, and the Task
            Decomposer's ambiguity gate genuinely fired — 0 tasks were generated. This is the real
            mechanism, not a description of what it should do.
          </p>
          <button type="button" onClick={() => onRequirementCreated(demo.requirementId)}>
            Open this requirement
          </button>
        </div>
      )}

      {demo.phase === 'unexpectedly-not-blocked' && (
        <p className="task-card__error">
          The gate did not block this run (plan status: {demo.plan.status}). This is unexpected —
          treat it as a finding, not a success, and inspect the requirement's ambiguity analysis
          before trusting this result.
        </p>
      )}

      <div className="screen-section">
        <h4>Interpretations presented to the engineer</h4>
        <p>
          The workbench does not choose between these. An engineer must pick one explicitly before
          any implementation work begins.
        </p>
        {INTERPRETATIONS.map((interp) => (
          <div key={interp.id} className="interpretation-card">
            <h4>
              {interp.id} — {interp.title} {interp.chosen && <span className="badge badge--engineer">Chosen by engineer</span>}
            </h4>
            <p>{interp.scope}</p>
            <div className="interpretation-card__columns">
              <div>
                <strong>Pros</strong>
                <ul>
                  {interp.pros.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>Cons</strong>
                <ul>
                  {interp.cons.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
        <p>
          Interpretation C was chosen and implemented with privacy mitigations (hashed IP, no
          fabricated geographic data) — see <code>ARCHITECTURE.md</code> (Key Design Decisions).
          This reused implementation is not repeated by this demo button; the button above
          demonstrates the gate itself using a fresh requirement so it can be re-run at any time.
        </p>
        <button type="button" onClick={() => onNavigate('report')}>
          See the Final Report for how this was ultimately resolved
        </button>
      </div>
    </div>
  )
}
