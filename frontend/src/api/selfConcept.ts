import { OpenAPI } from "@/client"
import { request } from "@/client/core/request"

export interface BaselineDeltaDimension {
  name: string
  baseline: number | null
  current: number | null
  delta: number | null
}

export interface BaselineDeltaResponse {
  baseline_at: string
  dimensions: BaselineDeltaDimension[]
}

export const selfConceptApi = {
  getBaselineDelta: (): Promise<BaselineDeltaResponse> =>
    request(OpenAPI, {
      method: "GET",
      url: "/api/v1/scaffold/self-concept/baseline-delta",
    }),
}
