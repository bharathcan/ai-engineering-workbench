export function FlowSteps({ currentStep = 0 }: { currentStep?: number }) {
  const steps = [
    { id: 1, label: 'Requirement', description: 'Define the project' },
    { id: 2, label: 'Analysis', description: 'Analyze scope' },
    { id: 3, label: 'Planning', description: 'Create tasks' },
    { id: 4, label: 'Execute', description: 'Run AI' },
    { id: 5, label: 'Artifacts', description: 'Generate code' },
    { id: 6, label: 'Validate', description: 'Quality check' },
  ]

  return (
    <div className="flow-steps">
      <h3 className="flow-steps__title">Workflow</h3>
      <div className="flow-steps__list">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`flow-step ${index < currentStep ? 'flow-step--completed' : index === currentStep ? 'flow-step--active' : 'flow-step--pending'}`}
          >
            <div className="flow-step__number">{step.id}</div>
            <div className="flow-step__content">
              <div className="flow-step__label">{step.label}</div>
              <div className="flow-step__description">{step.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
