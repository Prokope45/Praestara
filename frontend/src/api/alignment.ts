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
}
