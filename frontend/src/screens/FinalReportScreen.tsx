import { flattenAiRuns, flattenArtifacts, flattenValidations, type ProjectData } from '../hooks/useProjectData'
import '../components/AppShell.css'

export function FinalReportScreen({ project }: { project: ProjectData | null }) {
  if (!project) {
    return (
      <section className="screen">
        <h2>Final Report</h2>
        <p className="app-shell__empty">Select a project first.</p>
      </section>
    )
  }

  const { requirement, plan, artifactsByTaskId, validationsByArtifactId } = project
  const aiRuns = flattenAiRuns(plan)
  const artifacts = flattenArtifacts(plan, artifactsByTaskId)
  const validations = flattenValidations(plan, artifactsByTaskId, validationsByArtifactId)

  const taskDecisions = (plan?.tasks ?? []).flatMap((t) =>
    t.decisions.map((d) => ({ scope: `Task ${t.id} — ${t.title}`, decision: d })),
  )
  const aiRunDecisions = aiRuns.flatMap(({ task, run }) =>
    run.decisions.map((d) => ({ scope: `AI Run ${run.id} (task ${task.id})`, decision: d })),
  )
  const artifactDecisions = artifacts.flatMap(({ task, artifact }) =>
    artifact.decisions.map((d) => ({ scope: `Artifact ${artifact.id} (task ${task.id})`, decision: d })),
  )
  const allDecisions = [...taskDecisions, ...aiRunDecisions, ...artifactDecisions]

  const notValidated = validations.filter((v) => v.validation.status === 'NOT_VALIDATED')
  const failed = validations.filter((v) => v.validation.status === 'FAILED')
  const passed = validations.filter((v) => v.validation.status === 'PASSED')

  const allRisks = plan?.risks.map((r) => r.description) ?? []
  const allAssumptions = [
    ...(requirement.latest_analysis?.assumptions.map((a) => a.description) ?? []),
    ...(plan?.assumptions ?? []),
  ]

  const handleExport = () => {
    const md = buildMarkdownReport({
      requirement,
      plan,
      allDecisions,
      artifacts,
      validations,
      allRisks,
      allAssumptions,
    })
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `final-report-${requirement.id}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <section className="screen">
      <h2>Final Report</h2>
      <button type="button" className="export-button" onClick={handleExport}>
        Export as Markdown
      </button>

      <div className="report-block">
        <h3>Original Requirement</h3>
        <p>{requirement.text}</p>
      </div>

      <div className="report-block">
        <h3>Engineering Decisions ({allDecisions.length})</h3>
        {allDecisions.length === 0 && <p className="app-shell__empty">No decisions recorded yet.</p>}
        <ul>
          {allDecisions.map(({ scope, decision }) => (
            <li key={decision.id}>
              <strong>{scope}:</strong> {decision.decision}
              {decision.rationale ? ` — ${decision.rationale}` : ''}
            </li>
          ))}
        </ul>
      </div>

      <div className="report-block">
        <h3>Implementation Summary</h3>
        {plan ? (
          <p>{plan.summary}</p>
        ) : (
          <p className="app-shell__empty">No engineering plan generated for this requirement.</p>
        )}
      </div>

      <div className="report-block">
        <h3>Generated Artifacts ({artifacts.length})</h3>
        <ul>
          {artifacts.map(({ task, artifact }) => (
            <li key={artifact.id}>
              {artifact.id} ({artifact.artifact_type}, v{artifact.version}, {artifact.status}) —
              task {task.id}
            </li>
          ))}
        </ul>
      </div>

      <div className="report-block">
        <h3>Validation Summary</h3>
        <p>
          {passed.length} passed, {failed.length} failed, {notValidated.length} NOT_VALIDATED, out
          of {validations.length} recorded.
        </p>
        {notValidated.length > 0 && (
          <>
            <p>
              <strong>NOT_VALIDATED means the validation was never executed</strong> — it is not a
              pass, and is not represented as one anywhere in this workbench.
            </p>
            <ul>
              {notValidated.map(({ validation, artifact }) => (
                <li key={validation.id}>
                  {validation.validation_type} on artifact {artifact.id}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="report-block">
        <h3>Risks</h3>
        {allRisks.length === 0 ? (
          <p className="app-shell__empty">None recorded.</p>
        ) : (
          <ul>
            {allRisks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="report-block">
        <h3>Assumptions</h3>
        {allAssumptions.length === 0 ? (
          <p className="app-shell__empty">None recorded.</p>
        ) : (
          <ul>
            {allAssumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="report-block">
        <h3>Limitations &amp; Remaining NOT_VALIDATED Items</h3>
        <p>
          AI outputs across this workbench are engineer-authored stand-ins for a live provider
          response — no live AI provider (e.g. a configured Anthropic API key) exists in this
          environment, so no run in this project reflects real model behavior. This is disclosed
          consistently rather than presented as a live AI call.
        </p>
        {plan?.unresolved_ambiguities && plan.unresolved_ambiguities.length > 0 && (
          <ul>
            {plan.unresolved_ambiguities.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

function buildMarkdownReport(data: {
  requirement: ProjectData['requirement']
  plan: ProjectData['plan']
  allDecisions: { scope: string; decision: { decision: string; rationale: string | null } }[]
  artifacts: { task: { id: string }; artifact: { id: string; artifact_type: string; version: number; status: string } }[]
  validations: { validation: { id: string; validation_type: string; status: string } }[]
  allRisks: string[]
  allAssumptions: string[]
}): string {
  const lines: string[] = []
  lines.push(`# Final Report — ${data.requirement.id}`, '')
  lines.push('## Original Requirement', '', data.requirement.text, '')
  lines.push('## Engineering Decisions', '')
  for (const { scope, decision } of data.allDecisions) {
    lines.push(`- **${scope}:** ${decision.decision}${decision.rationale ? ` — ${decision.rationale}` : ''}`)
  }
  lines.push('', '## Implementation Summary', '', data.plan?.summary ?? 'No plan generated.', '')
  lines.push('## Generated Artifacts', '')
  for (const { task, artifact } of data.artifacts) {
    lines.push(`- ${artifact.id} (${artifact.artifact_type}, v${artifact.version}, ${artifact.status}) — task ${task.id}`)
  }
  lines.push('', '## Validation Summary', '')
  const passed = data.validations.filter((v) => v.validation.status === 'PASSED').length
  const failed = data.validations.filter((v) => v.validation.status === 'FAILED').length
  const notValidated = data.validations.filter((v) => v.validation.status === 'NOT_VALIDATED').length
  lines.push(`${passed} passed, ${failed} failed, ${notValidated} NOT_VALIDATED, out of ${data.validations.length} recorded.`, '')
  lines.push('## Risks', '')
  for (const r of data.allRisks) lines.push(`- ${r}`)
  lines.push('', '## Assumptions', '')
  for (const a of data.allAssumptions) lines.push(`- ${a}`)
  lines.push(
    '',
    '## Limitations',
    '',
    'AI outputs across this workbench are engineer-authored stand-ins for a live provider ' +
      'response — no live AI provider is configured in this environment.',
  )
  return lines.join('\n')
}
