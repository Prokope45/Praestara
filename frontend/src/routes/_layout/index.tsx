import { Box, Container, Typography, Paper, Button, Stack } from "@mui/material"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { FiArrowRight } from "react-icons/fi"
import { Line, Radar } from "react-chartjs-2"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  RadialLinearScale,
  Filler,
  Tooltip,
  Legend,
} from "chart.js"

import useAuth from "@/hooks/useAuth"
import { CheckinsService, QuestionnairesService } from "@/client"
import { PendingQuestionnaireWidget } from "@/components/Questionnaires/PendingQuestionnaireWidget"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  RadialLinearScale,
  Filler,
  Tooltip,
  Legend
)

function Dashboard() {
  const { user: currentUser } = useAuth()
  const navigate = useNavigate()
  const triggerCheckin = (type: "morning" | "evening") => {
    localStorage.setItem(
      "praestara_checkin_force",
      JSON.stringify({ type, ts: Date.now() })
    )
    window.dispatchEvent(new Event("praestara_checkin_trigger"))
  }

  const { data: eveningHistory } = useQuery({
    queryKey: ["checkins", "evening"],
    queryFn: () =>
      CheckinsService.readCheckins({
        type: "evening",
        limit: 200,
      }),
  })

  // Fetch user's questionnaire assignments
  const { data: assignmentsData } = useQuery({
    queryKey: ["questionnaire-assignments", "me"],
    queryFn: () => QuestionnairesService.readMyAssignments({ skip: 0, limit: 100 }),
  })

  const adherenceSeries = useMemo(() => {
    const records = (eveningHistory?.data ?? []).slice().sort((a, b) => {
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    })

    const normalized = records
      .map((entry) => {
        const score = entry.alignment_score as number | undefined
        if (typeof score !== "number") return null
        return {
          date: new Date(entry.created_at).toLocaleDateString(),
          value: score,
        }
      })
      .filter(Boolean)

    if (normalized.length > 0) return normalized as { date: string; value: number }[]

    return [
      { date: "Week 1", value: 42 },
      { date: "Week 2", value: 46 },
      { date: "Week 3", value: 50 },
      { date: "Week 4", value: 55 },
      { date: "Week 5", value: 58 },
      { date: "Week 6", value: 62 },
      { date: "Week 7", value: 66 },
      { date: "Week 8", value: 70 },
    ]
  }, [eveningHistory])

  const adherenceChart = useMemo(() => {
    return {
      labels: adherenceSeries.map((point) => point.date),
      datasets: [
        {
          label: "Values/Self‑Concept Alignment",
          data: adherenceSeries.map((point) => point.value),
          borderColor: "#6D28D9",
          backgroundColor: "rgba(109, 40, 217, 0.15)",
          tension: 0.35,
          fill: true,
          pointRadius: 3,
        },
      ],
    }
  }, [adherenceSeries])

  const trajectoryData = useMemo(() => {
    const labels = ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"]
    return {
      labels,
      datasets: [
        {
          label: "Values-action coherence",
          data: [42, 44, 46, 48, 51, 55, 57, 60],
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124, 58, 237, 0.08)",
          tension: 0.35,
        },
        {
          label: "Identity continuity",
          data: [50, 49, 51, 52, 54, 56, 55, 58],
          borderColor: "#ec4899",
          backgroundColor: "rgba(236, 72, 153, 0.08)",
          tension: 0.35,
        },
        {
          label: "Agency / self-efficacy",
          data: [38, 40, 41, 43, 46, 48, 51, 53],
          borderColor: "#22c55e",
          backgroundColor: "rgba(34, 197, 94, 0.08)",
          tension: 0.35,
        },
        {
          label: "Emotional stability",
          data: [35, 36, 34, 38, 41, 44, 46, 47],
          borderColor: "#f97316",
          backgroundColor: "rgba(249, 115, 22, 0.08)",
          tension: 0.35,
        },
        {
          label: "Domain balance",
          data: [28, 30, 33, 35, 36, 39, 41, 43],
          borderColor: "#0ea5e9",
          backgroundColor: "rgba(14, 165, 233, 0.08)",
          tension: 0.35,
        },
      ],
    }
  }, [])

  const radarData = useMemo(() => {
    const labels = ["Health", "Contribution", "Relationships", "Growth", "Meaning"]
    return {
      labels,
      datasets: [
        {
          label: "3 weeks ago",
          data: [42, 58, 31, 40, 46],
          borderColor: "#94a3b8",
          backgroundColor: "rgba(148, 163, 184, 0.15)",
        },
        {
          label: "2 weeks ago",
          data: [48, 60, 33, 44, 49],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.15)",
        },
        {
          label: "Last week",
          data: [52, 62, 35, 46, 50],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.18)",
        },
        {
          label: "This week",
          data: [58, 64, 41, 49, 53],
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124, 58, 237, 0.18)",
        },
      ],
    }
  }, [])

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6, pb: 4 }}>
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={3}
          alignItems={{ xs: "flex-start", md: "flex-start" }}
          justifyContent="space-between"
          sx={{ mb: 4 }}
        >
          <Box>
            <Typography variant="h4" component="h1" sx={{ mb: 1 }}>
              Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Welcome back! Here's your progress overview.
            </Typography>
          </Box>

          <Stack direction="row" spacing={2} sx={{ alignSelf: { md: "flex-start" } }}>
            <Paper
              onClick={() => triggerCheckin("morning")}
              sx={{
                width: 140,
                height: 140,
                cursor: "pointer",
                p: 2,
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                background: "linear-gradient(135deg, #FDBA74 0%, #FDE68A 45%, #93C5FD 100%)",
                color: "#1f2937",
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                Morning
              </Typography>
              <Typography variant="body2">Projective check‑in</Typography>
            </Paper>
            <Paper
              onClick={() => triggerCheckin("evening")}
              sx={{
                width: 140,
                height: 140,
                cursor: "pointer",
                p: 2,
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                background: "linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #b45309 75%, #7f1d1d 100%)",
                color: "#f8fafc",
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                Evening
              </Typography>
              <Typography variant="body2">Reflective check‑in</Typography>
            </Paper>
          </Stack>
        </Stack>

        {(() => {
          // Find the first pending assignment (prioritize onboarding)
          const pendingAssignments = assignmentsData?.data?.filter(
            (assignment) => assignment.status === "PENDING"
          ) || []
          
          const onboardingAssignment = pendingAssignments.find(
            (assignment) => assignment.questionnaire.title === "Praestara Onboarding"
          )
          
          const firstPendingAssignment = onboardingAssignment || pendingAssignments[0]
          
          if (firstPendingAssignment) {
            return (
              <Box sx={{ mb: 4 }}>
                <PendingQuestionnaireWidget assignment={firstPendingAssignment} />
              </Box>
            )
          }
          
          return null
        })()}

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: "bold", mb: 1 }}>
            Alignment over time
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Values/self‑concept adherence across the last four months.
          </Typography>
          <Box sx={{ height: 320 }}>
            <Line
              data={adherenceChart}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                },
                scales: {
                  y: { min: 0, max: 100, ticks: { stepSize: 20 } },
                },
              }}
            />
          </Box>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: "bold", mb: 1 }}>
            Trajectory overview
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Longitudinal trends across key self-concept and value alignment axes.
          </Typography>
          <Box sx={{ height: 320 }}>
            <Line
              data={trajectoryData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "bottom" } },
                scales: { y: { min: 0, max: 100, ticks: { stepSize: 20 } } },
              }}
            />
          </Box>
        </Paper>

        {/* Value Map Snapshot */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
            <Typography variant="h5" sx={{ fontWeight: "bold" }}>
              Value map snapshot
            </Typography>
            <Button
              variant="outlined"
              endIcon={<FiArrowRight />}
              onClick={() => navigate({ to: "/value-map" })}
            >
              View Value Map
            </Button>
          </Box>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: "bold", mb: 1 }}>
            Value balance (last 4 weeks)
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Weekly snapshots of value-domain alignment.
          </Typography>
          <Box sx={{ height: 320 }}>
            <Radar
              data={radarData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  r: { min: 0, max: 100, ticks: { stepSize: 20 } },
                },
              }}
            />
          </Box>
        </Paper>

        {/* Quick Actions */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: "bold", mb: 3 }}>
            Quick Actions
          </Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <Button
              variant="outlined"
              fullWidth
              sx={{ py: 2 }}
              onClick={() => navigate({ to: "/value-map" })}
            >
              View Value Map
            </Button>
            <Button
              variant="outlined"
              fullWidth
              sx={{ py: 2 }}
              onClick={() => navigate({ to: "/settings" })}
            >
              Settings
            </Button>
            <Button
              variant="contained"
              fullWidth
              sx={{ py: 2 }}
              onClick={() => navigate({ to: "/value-map" })}
            >
              Open Value Map
            </Button>
          </Stack>
        </Paper>
      </Box>
    </Container>
  )
}
