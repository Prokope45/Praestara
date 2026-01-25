// Types for Orientations - Self-concept and purpose tracking

export interface OrientationTrait {
  id: string
  name: string
  value: number // 0-100 scale for radar chart
  description?: string | null
}

export interface OrientationPublic {
  id: string
  title: string // e.g., "I want to be a friendlier person"
  description?: string | null
  traits?: OrientationTrait[] // Peripheral traits that make up the goal
  notes?: string | null // User's reflections
  owner_id?: string // Added to match API type
  createdAt?: string // For local storage only
  updatedAt?: string // For local storage only
}

export interface OrientationMetrics {
  totalTraits: number
  averageValue: number
  highestTrait: OrientationTrait | null
  lowestTrait: OrientationTrait | null
}
