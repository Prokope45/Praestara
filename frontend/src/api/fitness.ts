import { OpenAPI } from "@/client"
import { request } from "@/client/core/request"

export interface WeeklyFitnessPlanPublic {
  id: string
  user_id: string
  cycle_id: string
  week_start: string
  week_end: string
  target_sessions: number
  domain_allocation: Record<string, number>
  selected_exercises: unknown[]
  session_outlines: unknown[] | null
  stress_budget: Record<string, number>
  metadata: Record<string, unknown>
  engine_version: string
  allocation_version: string
  progression_version: string
  exercise_library_version: string
  completed_sessions: number
  adherence_met: boolean | null
  status: string
  created_at: string
}

export interface FitnessPlanGenerateRequest {
  week_start?: string | null
  force_regen?: boolean
}

export interface FitnessSessionLogCreate {
  plan_id: string
  session_definition_id?: string | null
  session_date: string
  completed: boolean
  adherence_flag?: string | null
  perceived_effort?: number | null
  energy_level?: number | null
  duration_minutes?: number | null
  executed_stress?: number | null
  notes?: string | null
  actual_exercises?: unknown[] | null
}

export interface FitnessSessionLogPublic {
  id: string
  plan_id: string
  session_definition_id: string | null
  session_date: string
  completed: boolean
  adherence_flag: string
  perceived_effort: number | null
  energy_level: number | null
  duration_minutes: number | null
  executed_stress: number | null
  notes: string | null
  actual_exercises: unknown[] | null
  created_at: string
}

export interface FitnessWeekReflection {
  plan_id: string
  goal_met: boolean
  sessions_completed?: number | null
  reported_energy?: number | null
  fatigue_flags?: string[] | null
  perceived_difficulty?: number | null
  injury_signals?: string[] | null
  recovery_adequacy?: number | null
}

export interface FitnessExposureEventRead {
  id: string
  week_id: string
  session_id: string | null
  planned_stress: number
  executed_stress: number | null
  duration_minutes: number | null
  adherence_flag: string
  burnout_snapshot: number | null
  domain_distribution: Record<string, number>
  timestamp: string
}

export interface FitnessExposureEventReadResponse {
  events: FitnessExposureEventRead[]
}

export const fitnessApi = {
  generatePlan: (payload: FitnessPlanGenerateRequest) =>
    request<WeeklyFitnessPlanPublic>(OpenAPI, {
      method: "POST",
      url: "/api/v1/scaffold/fitness/plan/generate",
      body: payload,
      mediaType: "application/json",
    }),
  getCurrentPlan: () =>
    request<WeeklyFitnessPlanPublic>(OpenAPI, {
      method: "GET",
      url: "/api/v1/scaffold/fitness/plan/current",
    }),
  logSession: (payload: FitnessSessionLogCreate) =>
    request<FitnessSessionLogPublic>(OpenAPI, {
      method: "POST",
      url: "/api/v1/scaffold/fitness/session/log",
      body: payload,
      mediaType: "application/json",
    }),
  submitWeekReflection: (payload: FitnessWeekReflection) =>
    request<WeeklyFitnessPlanPublic>(OpenAPI, {
      method: "POST",
      url: "/api/v1/scaffold/fitness/week/reflection",
      body: payload,
      mediaType: "application/json",
    }),
  getExposureEvents: (params?: {
    start_date?: string
    end_date?: string
    week_id?: string
  }) =>
    request<FitnessExposureEventReadResponse>(OpenAPI, {
      method: "GET",
      url: "/api/v1/scaffold/fitness/exposure/events",
      query: params,
    }),
}
