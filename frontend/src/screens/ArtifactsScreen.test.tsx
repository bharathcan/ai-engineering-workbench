import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as artifactsApi from '../api/artifacts'
import { artifactFixture, fullProjectFixture } from '../test/fixtures'
import { ArtifactsScreen } from './ArtifactsScreen'

vi.mock('../api/artifacts', async () => {
  const actual = await vi.importActual<typeof import('../api/artifacts')>('../api/artifacts')
  return {
    ...actual,
    decideArtifact: vi.fn(),
  }
})

describe('ArtifactsScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays artifact type, version, status, task, and AI run', () => {
    render(<ArtifactsScreen project={fullProjectFixture} onChanged={vi.fn()} />)

    expect(screen.getByText(artifactFixture.id)).toBeInTheDocument()
    expect(screen.getByText('SOURCE_CODE')).toBeInTheDocument()
    expect(screen.getByText('v1')).toBeInTheDocument()
    expect(screen.getByText(artifactFixture.ai_run_id)).toBeInTheDocument()
    expect(screen.getByText(/AI-generated artifact/i)).toBeInTheDocument()
  })

  it('reveals source content on demand', async () => {
    const user = userEvent.setup()
    render(<ArtifactsScreen project={fullProjectFixture} onChanged={vi.fn()} />)

    expect(screen.queryByText(/create_short_url/)).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Show Source/i }))
    expect(screen.getByText(/create_short_url/)).toBeInTheDocument()
  })

  it('submits an ACCEPT decision for a pending artifact', async () => {
    const user = userEvent.setup()
    const onChanged = vi.fn()
    vi.mocked(artifactsApi.decideArtifact).mockResolvedValue({ ...artifactFixture, status: 'APPROVED' })

    render(<ArtifactsScreen project={fullProjectFixture} onChanged={onChanged} />)
    await user.click(screen.getByRole('button', { name: 'Accept' }))

    await waitFor(() =>
      expect(artifactsApi.decideArtifact).toHaveBeenCalledWith(artifactFixture.id, 'ACCEPT', undefined),
    )
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
  })
})
