import type { EngineeringTask } from '../api/tasks'

export function TasksGrid({
  tasks,
  selectedTaskId,
  onSelectTask,
}: {
  tasks: EngineeringTask[]
  selectedTaskId: string | null
  onSelectTask: (taskId: string) => void
}) {
  return (
    <div className="tasks-grid">
      {tasks.map((task) => (
        <button
          key={task.id}
          className={`task-card-grid ${task.id === selectedTaskId ? 'task-card-grid--selected' : ''}`}
          onClick={() => onSelectTask(task.id)}
        >
          <div className="task-card-grid__header">
            <span className="task-card-grid__id">{task.id}</span>
            <span className={`task-card-grid__status task-card-grid__status--${task.review_status.toLowerCase()}`}>
              {task.review_status}
            </span>
          </div>

          <h4 className="task-card-grid__title">{task.title}</h4>

          <div className="task-card-grid__type">{task.type}</div>

          <div className="task-card-grid__meta">
            <div className="task-card-grid__priority">Priority: {task.sequence}</div>
            <div className="task-card-grid__status-value">{task.status}</div>
          </div>

          <div className="task-card-grid__footer">
            {task.dependencies.length > 0 && (
              <span className="task-card-grid__dependency">
                Depends: {task.dependencies.join(', ')}
              </span>
            )}
          </div>
        </button>
      ))}
    </div>
  )
}
