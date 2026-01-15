// TEMPORARY STORAGE UTILITY - FOR DEVELOPMENT ONLY
// This file provides localStorage-based storage for objectives until backend is implemented
// Data stored here will be lost when localStorage is cleared

import type { ObjectivePublic } from "../types/objectives"

const STORAGE_KEY = "temp_objectives"

export const getTempObjectives = (): ObjectivePublic[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch (error) {
    console.error("Error reading temp objectives:", error)
    return []
  }
}

export const saveTempObjective = (objective: ObjectivePublic): void => {
  try {
    const objectives = getTempObjectives()
    const existingIndex = objectives.findIndex((o) => o.id === objective.id)
    
    if (existingIndex >= 0) {
      // Update existing
      objectives[existingIndex] = objective
    } else {
      // Add new
      objectives.push(objective)
    }
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(objectives))
  } catch (error) {
    console.error("Error saving temp objective:", error)
  }
}

export const deleteTempObjective = (id: string): void => {
  try {
    const objectives = getTempObjectives()
    const filtered = objectives.filter((o) => o.id !== id)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  } catch (error) {
    console.error("Error deleting temp objective:", error)
  }
}

export const clearTempObjectives = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (error) {
    console.error("Error clearing temp objectives:", error)
  }
}
