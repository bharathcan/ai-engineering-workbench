import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fullProjectFixture, requirementFixture } from '../test/fixtures'
import { FinalReportScreen } from './FinalReportScreen'

describe('FinalReportScreen', () => {
  it('shows an empty state when no project is selected', () => {
    render(<FinalReportScreen project={null} />)
    expect(screen.getByText(/Select a project first/i)).toBeInTheDocument()
  })

  it('renders the original requirement, decisions, artifacts, and a validation summary that separates NOT_VALIDATED from passed', () => {
    render(<FinalReportScreen project={fullProjectFixture} />)

    expect(screen.getByText(requirementFixture.text)).toBeInTheDocument()
    expect(screen.getByText(/1 passed, 0 failed, 1 NOT_VALIDATED/)).toBeInTheDocument()
    expect(
      screen.getByText(/NOT_VALIDATED means the validation was never executed/i),
    ).toBeInTheDocument()
    // ART-001 legitimately appears twice: once in Generated Artifacts, once
    // in the NOT_VALIDATED breakdown under Validation Summary.
    expect(screen.getAllByText(/ART-001/).length).toBe(2)
    expect(screen.getByRole('button', { name: /Export as Markdown/i })).toBeInTheDocument()
  })
})
