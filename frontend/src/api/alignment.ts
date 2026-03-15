import { OpenAPI } from "@/client"
import { request } from "@/client/core/request"

export interface AlignmentCommitment {
  module: string
  commitment_id: string
  label: string
  context?: Record<string, unknown> | null
}

export interface AlignmentDailyResponse {
  date: string
  commitments: AlignmentCommitment[]
}

export interface AlignmentCompletion {
  module: string
  commitment_id: string
  completed: boolean
  context?: Record<string, unknown> | null
}

export interface AlignmentDailyRequest {
  date: string
  commitments_completed: AlignmentCompletion[]
}

export interface AlignmentDailyResult {
  module: string
  status: string
}

export interface AlignmentDailyPostResponse {
  date: string
  results: AlignmentDailyResult[]
}

export interface AlignmentWeeklyModuleSummary {
  module: string
  adherence_rate: number
  capacity_delta: number
  burnout_index: number | null
  constraint_mismatch_count: number
  exposure_density: number
}

export interface AlignmentWeeklySummaryResponse {
  week_start: string
  summaries: AlignmentWeeklyModuleSummary[]
}

export interface AlignmentWeeklyAdjustment {
  module: string
  target_sessions?: number | null
  priority_shift?: string | null
  constraint_updates?: Record<string, unknown> | null
}

export interface AlignmentWeeklyMeetingRequest {
  week_start: string
  adjustments: AlignmentWeeklyAdjustment[]
}

export interface AlignmentWeeklyMeetingResponse {
  week_start: string
  results: AlignmentDailyResult[]
}

export interface AlignmentHistoryEntry {
  date: string
  commitments: string[]
  reflection_status: string
  modules_affected: string[]
  exposure_links: string[]
  constraint_snapshot: Record<string, unknown>
}

export interface AlignmentHistoryResponse {
  timeline: AlignmentHistoryEntry[]
}

export interface AlignmentSurfaceWeekSummary {
  goal_name: string
  target: number
  completed: number
  days_remaining: number
}

export interface AlignmentSurfaceCommitment {
  goal_name: string
  planned_today: boolean
  completed_today: boolean | null
  commitment_id: string
  module: string
}

export interface AlignmentSurfaceTextContext {
  projection_text: string
  reflection_text: string
}

export interface AlignmentSurfaceResponse {
  date: string
  week_summary: AlignmentSurfaceWeekSummary[]
  today_commitments: AlignmentSurfaceCommitment[]
  text_context: AlignmentSurfaceTextContext
}

export interface AlignmentTodayRequest {
  commitments: Record<string, boolean>
  completion?: Record<string, boolean> | null
  note?: string | null
}

export interface AlignmentTodayResponse {
  date: string
  status: string
  decoded_signal?: Record<string, unknown> | null
}

export const alignmentApi = {
  getDaily: (day?: string) =>
    request<AlignmentDailyResponse>(OpenAPI, {
      method: "GET",
      url: "/api/v1/alignment/daily",
      query: day ? { day } : undefined,
    }),
  postDaily: (payload: AlignmentDailyRequest) =>
    request<AlignmentDailyPostResponse>(OpenAPI, {
      method: "POST",
      url: "/api/v1/alignment/daily",
      body: payload,
      mediaType: "application/json",
    }),
  getWeeklySummary: (week_start: string) =>
    request<AlignmentWeeklySummaryResponse>(OpenAPI, {
      method: "GET",
      url: "/api/v1/alignment/weekly-summary",
      query: { week_start },
    }),
  postWeeklyMeeting: (payload: AlignmentWeeklyMeetingRequest) =>
    request<AlignmentWeeklyMeetingResponse>(OpenAPI, {
      method: "POST",
      url: "/api/v1/alignment/weekly-meeting",
      body: payload,
      mediaType: "application/json",
    }),
  getHistory: () =>
    request<AlignmentHistoryResponse>(OpenAPI, {
      method: "GET",
      url: "/api/v1/alignment/history",
    }),
  getToday: (day?: string) =>
    request<AlignmentSurfaceResponse>(OpenAPI, {
      method: "GET",
      url: "/api/v1/alignment/today",
      query: day ? { day } : undefined,
    }),
  postToday: (payload: AlignmentTodayRequest) =>
    request<AlignmentTodayResponse>(OpenAPI, {
      method: "POST",
      url: "/api/v1/alignment/today",
      body: payload,
      mediaType: "application/json",
    }),
}
