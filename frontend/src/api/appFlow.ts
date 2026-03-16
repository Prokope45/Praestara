import { OpenAPI } from "@/client"
import { request } from "@/client/core/request"

export interface AppFlowState {
  current_phase: string
  pending_action: string | null
  has_baseline: boolean
  onboarding_completed: boolean
  week_setup_confirmed: boolean
  current_cycle_id: string | null
  current_week_start: string | null
  active_goal_count: number
}

export interface WeekSetupGoalProposal {
  goal_id: string
  goal_cycle_id: string
  title: string
  category: string
  target_value: number
  target_unit: string
  intensity_level: number
  suggested_days: string[]
  rationale: string
  confidence_signal: number
}

export interface WeekSetupResponse {
  current_phase: string
  current_cycle_id: string
  week_start: string
  weekly_available_hours: number
  stress_baseline: number
  latent_state: Record<string, number>
  physiology_state: Record<string, number>
  proposed_goals: WeekSetupGoalProposal[]
  narrative_prompt: string
  confirmed: boolean
}

export interface WeekSetupGoalUpdate {
  goal_id: string
  target_value?: number | null
  intensity_level?: number | null
  accepted: boolean
  note?: string | null
}

export interface WeekSetupSubmitRequest {
  goals: WeekSetupGoalUpdate[]
  schedule_note?: string | null
  reflection?: string | null
}

export interface WeekSetupSubmitResponse {
  status: string
  confirmed_at: string
}

export const appFlowApi = {
  getFlow: () =>
    request<AppFlowState>(OpenAPI, {
      method: "GET",
      url: "/api/v1/app/flow",
    }),
  getWeekSetup: () =>
    request<WeekSetupResponse>(OpenAPI, {
      method: "GET",
      url: "/api/v1/week-setup/current",
    }),
  submitWeekSetup: (payload: WeekSetupSubmitRequest) =>
    request<WeekSetupSubmitResponse>(OpenAPI, {
      method: "POST",
      url: "/api/v1/week-setup/current",
      body: payload,
      mediaType: "application/json",
    }),
}
