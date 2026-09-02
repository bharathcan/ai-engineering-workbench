import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as tasksApi from '../api/tasks'
import { fullProjectFixture, taskFixture } from '../test/fixtures'
import { TasksScreen } from './TasksScreen'

vi.mock('../api/tasks', async () => {
  const actual = await vi.importActual<typeof import('../api/tasks')>('../api/tasks')
  return {
    ...actual,
    decideTask: vi.fn(),
    requestAiAssist: vi.fn(),
  }
})

describe('TasksScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays task description, acceptance criteria, and review status', () => {
    render(<TasksScreen project={fullProjectFixture} onChanged={vi.fn()} />)

    expect(screen.getByText(taskFixture.title)).toBeInTheDocument()
    expect(screen.getByText(taskFixture.description)).toBeInTheDocument()
    expect(screen.getByText(/Short codes are unique\./)).toBeInTheDocument()
  })

  it('does not treat a pending task as decided, and blocks it behind Accept/Modify/Reject', () => {
    render(<TasksScreen project={fullProjectFixture} onChanged={vi.fn()} />)

    expect(screen.getByText(/requires an engineer decision/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Accept' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Modify' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument()
  })

  it('submits an ACCEPT decision and notifies the parent to refresh', async () => {
    const user = userEvent.setup()
    const onChanged = vi.fn()
    vi.mocked(tasksApi.decideTask).mockResolvedValue({ ...taskFixture, status: 'APPROVED', review_status: 'ACCEPT' })

    render(<TasksScreen project={fullProjectFixture} onChanged={onChanged} />)

    await user.click(screen.getByRole('button', { name: 'Accept' }))

    await waitFor(() =>
      expect(tasksApi.decideTask).toHaveBeenCalledWith(taskFixture.id, 'ACCEPT', undefined, undefined),
    )
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
  })
})
