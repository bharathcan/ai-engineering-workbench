import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as requirementsApi from '../api/requirements'
import { AppShell } from './AppShell'

vi.mock('../api/requirements', async () => {
  const actual = await vi.importActual<typeof import('../api/requirements')>('../api/requirements')
  return {
    ...actual,
    listRequirements: vi.fn(),
  }
})

describe('AppShell navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(requirementsApi.listRequirements).mockResolvedValue([])
  })

  it('renders every required navigation item and starts on the Dashboard', async () => {
    render(<AppShell />)
    await waitFor(() => expect(requirementsApi.listRequirements).toHaveBeenCalled())

    const nav = within(screen.getByRole('navigation', { name: /Workbench navigation/i }))
    for (const label of [
      'Dashboard',
      'Requirement',
      'Engineering Plan',
      'Tasks',
      'AI Runs',
      'Artifacts',
      'Validation',
      'Scenarios',
      'Final Report',
    ]) {
      expect(nav.getByRole('button', { name: label })).toBeInTheDocument()
    }

    // No project is selected yet, so the Dashboard renders its empty state.
    expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
  })

  it('switches the active screen when a nav item is clicked', async () => {
    const user = userEvent.setup()
    render(<AppShell />)
    await waitFor(() => expect(requirementsApi.listRequirements).toHaveBeenCalled())

    const nav = within(screen.getByRole('navigation', { name: /Workbench navigation/i }))

    await user.click(nav.getByRole('button', { name: 'AI Runs' }))
    expect(screen.getByRole('heading', { name: 'AI Runs' })).toBeInTheDocument()

    await user.click(nav.getByRole('button', { name: 'Scenarios' }))
    expect(screen.getByRole('heading', { name: 'Scenarios' })).toBeInTheDocument()
  })
})
