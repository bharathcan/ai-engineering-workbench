import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fullProjectFixture, notValidatedFixture, passedValidationFixture } from '../test/fixtures'
import { ValidationScreen } from './ValidationScreen'

describe('ValidationScreen', () => {
  it('renders both validations and visually distinguishes PASSED from NOT_VALIDATED', () => {
    render(<ValidationScreen project={fullProjectFixture} onChanged={vi.fn()} />)

    const passedBadge = screen.getByText('PASSED')
    const notValidatedBadge = screen.getByText('NOT_VALIDATED')

    expect(passedBadge).toBeInTheDocument()
    expect(notValidatedBadge).toBeInTheDocument()
    expect(passedBadge.className).not.toBe(notValidatedBadge.className)
    expect(passedBadge.className).toContain('badge--passed')
    expect(notValidatedBadge.className).toContain('badge--not-validated')

    expect(screen.getByText(/NOT_VALIDATED means the validation was never run/i)).toBeInTheDocument()
    expect(screen.getByText(passedValidationFixture.command)).toBeInTheDocument()
  })

  it('shows an explanatory notice instead of no state when nothing has been recorded', () => {
    render(
      <ValidationScreen
        project={{ ...fullProjectFixture, validationsByArtifactId: {} }}
        onChanged={vi.fn()}
      />,
    )
    expect(screen.getByText(/No validations recorded yet/i)).toBeInTheDocument()
    expect(screen.queryByText(notValidatedFixture.id)).not.toBeInTheDocument()
  })
})
