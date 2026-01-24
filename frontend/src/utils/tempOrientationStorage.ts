// Temporary localStorage utilities for orientations until backend is implemented

import type { OrientationPublic } from "../types/orientations"

const STORAGE_KEY = "praestara_temp_orientations"

export function getTempOrientations(): OrientationPublic[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch (error) {
    console.error("Error reading temp orientations from localStorage:", error)
    return []
  }
}

export function saveTempOrientation(orientation: OrientationPublic): void {
  try {
    const orientations = getTempOrientations()
    const existingIndex = orientations.findIndex((o) => o.id === orientation.id)

    if (existingIndex >= 0) {
      // Update existing
      orientations[existingIndex] = orientation
    } else {
      // Add new
      orientations.unshift(orientation)
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(orientations))
  } catch (error) {
    console.error("Error saving temp orientation to localStorage:", error)
  }
}

export function deleteTempOrientation(orientationId: string): void {
  try {
    const orientations = getTempOrientations()
    const filtered = orientations.filter((o) => o.id !== orientationId)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  } catch (error) {
    console.error("Error deleting temp orientation from localStorage:", error)
  }
}
