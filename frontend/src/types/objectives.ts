// Types for Objectives and Tasks

export enum TaskPriority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export interface TaskNode {
  id: string
  title: string
  description: string
  deadline: string // ISO date string
  priority: TaskPriority
  isActive: boolean
  position: { x: number; y: number }
}

export interface TaskEdge {
  id: string
  source: string
  target: string
}

export interface ObjectivePublic {
  id: string
  title: string
  description?: string
  tasks: TaskNode[]
  edges: TaskEdge[]
  createdAt: string
  updatedAt: string
}

export interface ObjectiveMetrics {
  totalTasks: number
  completedTasks: number
  activeTasks: number
  inactiveTasks: number
  percentComplete: number
}
