// Types for Orientations - Self-concept and purpose tracking

export interface OrientationTrait {
  id: string
  name: string
  value: number // 0-100 scale for radar chart
  description?: string
}

export interface OrientationPublic {
  id: string
  title: string // e.g., "I want to be a friendlier person"
  description?: string
  traits: OrientationTrait[] // Peripheral traits that make up the goal
  createdAt: string
  updatedAt: string
  notes?: string // User's reflections
}

export interface OrientationMetrics {
  totalTraits: number
  averageValue: number
  highestTrait: OrientationTrait | null
  lowestTrait: OrientationTrait | null
}
