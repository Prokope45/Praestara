import { OpenAPI } from "@/client"
import { request } from "@/client/core/request"

export interface DevPresetResponse {
  status: string
  preset?: string
  assignment_id?: string | null
  response_id?: string | null
  cycle_id?: string | null
  week_setup_confirmed?: boolean | null
  user_id?: string
}

export const devPresetsApi = {
  apply: (mode: "week_setup" | "today_ready") =>
    request<DevPresetResponse>(OpenAPI, {
      method: "POST",
      url: "/api/v1/private/dev/apply-onboarding-preset",
      body: {
        preset: "balanced_baseline",
        confirm_week_setup: mode === "today_ready",
      },
      mediaType: "application/json",
    }),
  reset: () =>
    request<DevPresetResponse>(OpenAPI, {
      method: "POST",
      url: "/api/v1/private/dev/reset-state",
    }),
}
