import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as requirementsApi from '../api/requirements'
import { fullProjectFixture, requirementFixture } from '../test/fixtures'
import { RequirementScreen } from './RequirementScreen'

vi.mock('../api/requirements', async () => {
  const actual = await vi.importActual<typeof import('../api/requirements')>('../api/requirements')
  return {
    ...actual,
    createRequirement: vi.fn(),
    analyzeRequirement: vi.fn(),
  }
})

describe('RequirementScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the original requirement text and its analysis, distinguishing AI-suggested content', () => {
    render(
      <RequirementScreen project={fullProjectFixture} onRequirementCreated={vi.fn()} onAnalyzed={vi.fn()} />,
    )

    expect(screen.getByText(requirementFixture.text)).toBeInTheDocument()
    expect(screen.getByText(/AI-suggested analysis/i)).toBeInTheDocument()
    expect(screen.getByText('FR-001')).toBeInTheDocument()
    expect(screen.getByText(/Shorten a long URL\./)).toBeInTheDocument()
    expect(screen.getByText(/Custom alias length is unspecified/)).toBeInTheDocument()
  })

  it('submits a new requirement and reports the created id', async () => {
    const user = userEvent.setup()
    const onRequirementCreated = vi.fn()
    vi.mocked(requirementsApi.createRequirement).mockResolvedValue({
      ...requirementFixture,
      id: 'REQ-NEW',
      latest_analysis: null,
    })

    render(
      <RequirementScreen project={null} onRequirementCreated={onRequirementCreated} onAnalyzed={vi.fn()} />,
    )

    await user.type(screen.getByLabelText(/Requirement Input/i), 'Build a URL shortener.')
    await user.click(screen.getByRole('button', { name: /Create Requirement/i }))

    await waitFor(() => expect(onRequirementCreated).toHaveBeenCalledWith('REQ-NEW'))
  })
})
