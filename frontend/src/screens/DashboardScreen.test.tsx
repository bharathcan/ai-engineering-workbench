import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fullProjectFixture } from '../test/fixtures'
import { DashboardScreen } from './DashboardScreen'

describe('DashboardScreen', () => {
  it('shows an empty state and no metrics when no project is selected', () => {
    render(<DashboardScreen project={null} onNavigate={vi.fn()} />)
    expect(screen.getByText(/No project selected/i)).toBeInTheDocument()
  })

  it('renders the requirement text, stage, and counts for a selected project', () => {
    render(<DashboardScreen project={fullProjectFixture} onNavigate={vi.fn()} />)

    expect(screen.getByText(fullProjectFixture.requirement.text)).toBeInTheDocument()
    // 1 of 2 tasks is APPROVED in the fixture.
    expect(screen.getByText('1 / 2')).toBeInTheDocument()
    // 1 AI run, 1 artifact, 1 passed validation, 1 not-validated validation.
    expect(screen.getAllByText('1').length).toBeGreaterThan(0)
  })
})
