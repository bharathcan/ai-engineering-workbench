import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as requirementsApi from '../api/requirements'
import * as tasksApi from '../api/tasks'
import { planFixture, requirementFixture } from '../test/fixtures'
import { ScenariosScreen } from './ScenariosScreen'

vi.mock('../api/requirements', async () => {
  const actual = await vi.importActual<typeof import('../api/requirements')>('../api/requirements')
  return {
    ...actual,
    createRequirement: vi.fn(),
    analyzeRequirement: vi.fn(),
  }
})

vi.mock('../api/tasks', async () => {
  const actual = await vi.importActual<typeof import('../api/tasks')>('../api/tasks')
  return {
    ...actual,
    generatePlan: vi.fn(),
  }
})

describe('ScenariosScreen — Ambiguous tab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does not implement anything automatically, and shows the BLOCKED gate result when the plan is genuinely blocked', async () => {
    const user = userEvent.setup()
    vi.mocked(requirementsApi.createRequirement).mockResolvedValue({
      ...requirementFixture,
      id: 'REQ-AMBIGUOUS',
      text: 'Improve the analytics.',
      latest_analysis: null,
    })
    vi.mocked(requirementsApi.analyzeRequirement).mockResolvedValue({
      ...requirementFixture,
      id: 'REQ-AMBIGUOUS',
    })
    vi.mocked(tasksApi.generatePlan).mockResolvedValue({
      ...planFixture,
      status: 'BLOCKED',
      blocked_reason: 'HIGH-impact ambiguity: "improve" is not defined.',
      tasks: [],
    })

    render(<ScenariosScreen project={null} onRequirementCreated={vi.fn()} onNavigate={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: 'Ambiguous' }))
    await user.click(screen.getByRole('button', { name: /Submit "Improve the analytics/i }))

    await waitFor(() => expect(screen.getByText('BLOCKED — ENGINEER INPUT REQUIRED')).toBeInTheDocument())
    expect(screen.getByText(/"improve" is not defined/)).toBeInTheDocument()
  })

  it('flags an unexpectedly-unblocked result as a finding rather than treating it as success', async () => {
    const user = userEvent.setup()
    vi.mocked(requirementsApi.createRequirement).mockResolvedValue({
      ...requirementFixture,
      id: 'REQ-AMBIGUOUS-2',
      latest_analysis: null,
    })
    vi.mocked(requirementsApi.analyzeRequirement).mockResolvedValue(requirementFixture)
    vi.mocked(tasksApi.generatePlan).mockResolvedValue({ ...planFixture, status: 'GENERATED' })

    render(<ScenariosScreen project={null} onRequirementCreated={vi.fn()} onNavigate={vi.fn()} />)
    await user.click(screen.getByRole('button', { name: 'Ambiguous' }))
    await user.click(screen.getByRole('button', { name: /Submit "Improve the analytics/i }))

    await waitFor(() => expect(screen.getByText(/unexpected/i)).toBeInTheDocument())
  })

  it('shows the interpretations without auto-selecting one', async () => {
    const user = userEvent.setup()
    render(<ScenariosScreen project={null} onRequirementCreated={vi.fn()} onNavigate={vi.fn()} />)
    await user.click(screen.getByRole('button', { name: 'Ambiguous' }))
    expect(screen.getByText(/Reporting Analytics/)).toBeInTheDocument()
    expect(screen.getByText(/Real-Time Analytics/)).toBeInTheDocument()
    expect(screen.getByText(/Advanced User Analytics/)).toBeInTheDocument()
    expect(screen.getByText('Chosen by engineer')).toBeInTheDocument()
  })
})
