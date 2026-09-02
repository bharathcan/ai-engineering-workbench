import { useEffect, useRef } from 'react'
import type { EngineeringTask } from '../api/tasks'

interface ProjectNetworkProps {
  tasks?: EngineeringTask[]
}

export function ProjectNetwork({ tasks = [] }: ProjectNetworkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    // Create nodes from tasks
    interface Node {
      x: number
      y: number
      vx: number
      vy: number
      radius: number
      task?: EngineeringTask
    }

    const nodes: Node[] = []
    const nodeCount = Math.min(tasks.length || 8, 15)

    // Create nodes - if tasks exist, use them; otherwise create placeholder nodes
    if (tasks.length > 0) {
      tasks.slice(0, nodeCount).forEach((task, i) => {
        const angle = (i / nodeCount) * Math.PI * 2
        const radius = 80
        nodes.push({
          x: canvas.width / 2 + Math.cos(angle) * radius,
          y: canvas.height / 2 + Math.sin(angle) * radius,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          radius: 4,
          task,
        })
      })
    } else {
      // Create placeholder nodes in circular pattern
      for (let i = 0; i < nodeCount; i++) {
        const angle = (i / nodeCount) * Math.PI * 2
        const radius = 80
        nodes.push({
          x: canvas.width / 2 + Math.cos(angle) * radius,
          y: canvas.height / 2 + Math.sin(angle) * radius,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          radius: 4,
        })
      }
    }

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Update and draw nodes
      nodes.forEach((node) => {
        node.x += node.vx
        node.y += node.vy

        // Bounce off walls
        if (node.x < 20 || node.x > canvas.width - 20) node.vx *= -1
        if (node.y < 20 || node.y > canvas.height - 20) node.vy *= -1

        // Keep within bounds
        node.x = Math.max(20, Math.min(canvas.width - 20, node.x))
        node.y = Math.max(20, Math.min(canvas.height - 20, node.y))

        // Determine color based on task status
        let nodeColor = 'rgba(37, 99, 235, 0.7)'
        if (node.task?.status === 'APPROVED') {
          nodeColor = 'rgba(16, 185, 129, 0.7)'
        } else if (node.task?.status === 'BLOCKED') {
          nodeColor = 'rgba(239, 68, 68, 0.7)'
        } else if (node.task?.status === 'IN_PROGRESS') {
          nodeColor = 'rgba(251, 146, 60, 0.7)'
        }

        ctx.fillStyle = nodeColor
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
        ctx.fill()
      })

      // Draw connections - connect nearby nodes
      nodes.forEach((n1, i) => {
        nodes.slice(i + 1).forEach((n2) => {
          const dx = n2.x - n1.x
          const dy = n2.y - n1.y
          const distance = Math.sqrt(dx * dx + dy * dy)

          // Connect nodes within distance
          if (distance < 150) {
            const opacity = 0.2 * (1 - distance / 150)
            ctx.strokeStyle = `rgba(37, 99, 235, ${opacity})`
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.moveTo(n1.x, n1.y)
            ctx.lineTo(n2.x, n2.y)
            ctx.stroke()
          }
        })
      })

      requestAnimationFrame(animate)
    }

    animate()

    // Handle resize
    const handleResize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [tasks])

  return (
    <div className="project-network">
      <canvas ref={canvasRef} style={{ display: 'block', width: '100%', height: '100%' }} />
      <div className="project-network__overlay"></div>
    </div>
  )
}
