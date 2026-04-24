import { Box, Typography } from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useMemo, useRef } from "react"
import SunburstChart from "sunburst-chart"
const Sunburst = (SunburstChart as any).default || SunburstChart
import { QuestionnairesService } from "../../client"
import useAuth from "../../hooks/useAuth"

import {
  type DomainRatingData,
  primarySchemas,
} from "./valueMapData"

// Map known labels to primary schema ids
function mapDomainToSchemaId(label: string): string {
  const lower = label.toLowerCase()
  if (lower.includes("health") || lower.includes("sleep")) return "domain_health"
  if (lower.includes("work")) return "domain_execution"
  if (lower.includes("learning") || lower.includes("skill")) return "domain_proficiency"
  if (lower.includes("relationship") || lower.includes("family") || lower.includes("friend")) return "domain_philanthropy"
  if (lower.includes("community") || lower.includes("service")) return "domain_philanthropy"
  if (lower.includes("spiritual") || lower.includes("existential")) return "domain_faith"
  if (lower.includes("play") || lower.includes("enjoyment")) return "domain_virtue"
  if (lower.includes("order") || lower.includes("responsibility") || lower.includes("maintenance")) return "domain_strategy"
  
  return "domain_precision"
}

// Map each schema to a base color
const schemaColors: Record<string, string> = {
  domain_virtue: "#8b5cf6",
  domain_strategy: "#ec4899",
  domain_execution: "#f43f5e",
  domain_precision: "#f59e0b",
  domain_health: "#10b981",
  domain_proficiency: "#0ea5e9",
  domain_faith: "#3b82f6",
  domain_philanthropy: "#6366f1",
}

function shortenLabel(label: string): string {
  if (label.length > 15) {
    const parts = label.split(/\s+and\s+|\s+or\s+|,/i)
    if (parts.length > 1) {
      return parts[0].trim()
    }
  }
  return label
}

const fallbackDomainRatings: DomainRatingData[] = [
  { label: "Health and body care", importance: 8, consistency: 6 },
  { label: "Sleep and recovery", importance: 9, consistency: 7 },
  { label: "Work or contribution", importance: 8, consistency: 8 },
  { label: "Learning or skill building", importance: 7, consistency: 5 },
  { label: "Relationships and friendships", importance: 9, consistency: 8 },
  { label: "Family or close bonds", importance: 10, consistency: 9 },
  { label: "Community or service", importance: 6, consistency: 4 },
  { label: "Spiritual or existential life", importance: 8, consistency: 8 },
  { label: "Play, rest, enjoyment", importance: 7, consistency: 6 },
  { label: "Order, responsibility, life maintenance", importance: 8, consistency: 7 },
]

export interface ValueMapSunburstChartProps {
  width?: number
  height?: number
}

export function ValueMapSunburstChart({ width = 600, height = 600 }: ValueMapSunburstChartProps) {
  const { user } = useAuth()
  const chartRef = useRef<HTMLDivElement>(null)

  const { data: responsesData } = useQuery({
    queryKey: ["myResponses"],
    queryFn: () => QuestionnairesService.readMyResponses({ limit: 100 }),
  })

  const replaceUserName = (displayName: string) => {
    if (user != undefined && displayName === user.full_name) {
      return "Central Identity"
    }
    return displayName
  }

  const chartData = useMemo(() => {
    let domainRatings: DomainRatingData[] = []
    
    if (responsesData?.data) {
      for (const response of responsesData.data) {
        if (response.answers) {
          for (const answer of response.answers) {
            if (answer.question?.scale_type === "DOMAIN_RATING" && answer.text_response) {
              try {
                const val = JSON.parse(answer.text_response)
                domainRatings.push({
                  id: answer.question_id,
                  label: answer.question.question_text,
                  importance: val.importance ?? 5,
                  consistency: val.consistency ?? 5,
                })
              } catch (e) {}
            }
          }
        }
      }
    }

    if (domainRatings.length === 0) {
      domainRatings = fallbackDomainRatings
    }

    // Group domains by schema
    const domainsBySchema: Record<string, DomainRatingData[]> = {}
    domainRatings.forEach(domain => {
      const parent = mapDomainToSchemaId(domain.label)
      if (!domainsBySchema[parent]) domainsBySchema[parent] = []
      domainsBySchema[parent].push(domain)
    })

    const children = primarySchemas.map(schema => {
      const domains = domainsBySchema[schema.id] || []
      
      if (domains.length === 0) {
        return {
          name: schema.label,
          color: schemaColors[schema.id] || "#94a3b8",
          value: 1 // Provide a value so the empty schema still renders
        }
      }

      return {
        name: schema.label,
        color: schemaColors[schema.id] || "#94a3b8",
        children: domains.map(domain => ({
          name: shortenLabel(domain.label),
          fullName: domain.label,
          // Use 'value' instead of 'size' since sunburst-chart defaults to d.value
          value: 1, 
          color: schemaColors[schema.id],
          importance: domain.importance,
          consistency: domain.consistency
        }))
      }
    })

    return {
      name: user?.full_name || "You",
      color: "#1e293b",
      children
    }
  }, [responsesData, user])

  useEffect(() => {
    if (!chartRef.current) return

    chartRef.current.innerHTML = ""

    const myChart = Sunburst()
      .data(chartData)
      .width(width)
      .height(height)
      .size('value')
      .color((d: any) => d.color || "#ccc")
      .centerRadius(0.2) // inner radius
      .showLabels(true)
      .labelOrientation("angular")
      .tooltipContent((d: any) => {
        const displayName = d.fullName || d.name
        if (d.importance !== undefined) {
          return `
            <div style="background: rgba(0,0,0,0.8); color: white; padding: 4px 8px; border-radius: 4px;">
              <strong>${displayName}</strong><br/>
              Importance: ${d.importance}<br/>
              Consistency: ${d.consistency}
            </div>
          `
        }
        return `
          <div style="background: rgba(0,0,0,0.8); color: white; padding: 4px 8px; border-radius: 4px;">
            <strong>${replaceUserName(displayName)}</strong>
          </div>
        `
      })

    myChart(chartRef.current)

    return () => {
      // cleanup if necessary
    }
  }, [chartData, width, height])

  return (
    <Box sx={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", position: "relative" }}>
      <Box ref={chartRef} />
      <Box sx={{ mt: 4, textAlign: "center" }}>
        <Typography variant="caption" color="text.secondary">
          Hover over sections to see details.
        </Typography>
      </Box>
    </Box>
  )
}
