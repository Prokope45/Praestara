import { Box, Button, Card, CardContent, Container, Paper, Stack, Typography } from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useMemo } from "react"
import { Line, Radar } from "react-chartjs-2"
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  RadialLinearScale,
  Tooltip,
} from "chart.js"
import { FiArrowRight } from "react-icons/fi"

import {
  GoalScaffoldGoalsService,
  GoalScaffoldSelfConceptService,
  QuestionnairesService,
} from "@/client"
import { appFlowApi } from "@/api/appFlow"
import { PendingQuestionnaireWidget } from "@/components/Questionnaires/PendingQuestionnaireWidget"
import useAuth from "@/hooks/useAuth"

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
  Legend,
)

function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const { data: latestSnapshot } = useQuery({
    queryKey: ["self-concept", "snapshot"],
    queryFn: () => GoalScaffoldSelfConceptService.goalScaffoldGetLatestSnapshot(),
  })

  const { data: snapshotHistory } = useQuery({
    queryKey: ["self-concept", "history"],
    queryFn: () =>
      GoalScaffoldSelfConceptService.goalScaffoldGetSnapshotHistory({
        limit: 12,
        offset: 0,
      }),
  })

  const { data: goalsData } = useQuery({
    queryKey: ["goal-scaffold", "goals"],
    queryFn: () => GoalScaffoldGoalsService.goalScaffoldListGoals({ limit: 20, skip: 0 }),
  })

  const { data: assignmentsData } = useQuery({
    queryKey: ["questionnaire-assignments", "me"],
    queryFn: () => QuestionnairesService.readMyAssignments({ skip: 0, limit: 100 }),
  })

  const { data: flow } = useQuery({
    queryKey: ["app-flow"],
    queryFn: appFlowApi.getFlow,
  })

  const dimensions = (latestSnapshot?.dimensions ?? {}) as Record<string, number>
  const history = snapshotHistory ?? []
  const activeGoals = goalsData?.data ?? []

  const pendingAssignments =
    assignmentsData?.data?.filter((assignment) => assignment.status === "PENDING") ?? []
  const onboardingAssignment = pendingAssignments.find(
    (assignment) => assignment.questionnaire.title === "Praestara Onboarding",
  )

  const alignmentSeries = useMemo(() => {
    return history
      .slice()
      .reverse()
      .map((entry) => ({
        label: new Date(entry.computed_at).toLocaleDateString(),
        value: Math.round((entry.identity_consistency_index ?? 0.5) * 100),
      }))
  }, [history])

  const adherenceChart = useMemo(() => {
    return {
      labels: alignmentSeries.map((point) => point.label),
      datasets: [
        {
          label: "Identity consistency",
          data: alignmentSeries.map((point) => point.value),
          borderColor: "#6D28D9",
          backgroundColor: "rgba(109, 40, 217, 0.15)",
          tension: 0.35,
          fill: true,
          pointRadius: 3,
        },
      ],
    }
  }, [alignmentSeries])

  const trajectoryData = useMemo(() => {
    const rows = history.slice().reverse()
    const labels = rows.map((entry) => new Date(entry.computed_at).toLocaleDateString())

    const seriesFor = (key: string, invert = false) =>
      rows.map((entry) => {
        const value = Number((entry.dimensions as Record<string, unknown>)?.[key] ?? 0.5)
        return Math.round((invert ? 1 - value : value) * 100)
      })

    return {
      labels,
      datasets: [
        {
          label: "Goal clarity",
          data: seriesFor("goal_clarity"),
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124, 58, 237, 0.08)",
          tension: 0.35,
        },
        {
          label: "Self-efficacy",
          data: seriesFor("self_efficacy"),
          borderColor: "#ec4899",
          backgroundColor: "rgba(236, 72, 153, 0.08)",
          tension: 0.35,
        },
        {
          label: "Motivation",
          data: seriesFor("motivation"),
          borderColor: "#22c55e",
          backgroundColor: "rgba(34, 197, 94, 0.08)",
          tension: 0.35,
        },
        {
          label: "Stress regulation",
          data: seriesFor("stress_load", true),
          borderColor: "#0ea5e9",
          backgroundColor: "rgba(14, 165, 233, 0.08)",
          tension: 0.35,
        },
      ],
    }
  }, [history])

  const radarData = useMemo(() => {
    const labels = [
      "Clarity",
      "Agency",
      "Motivation",
      "Resilience",
      "Well-being",
      "Stress regulation",
    ]
    return {
      labels,
      datasets: [
        {
          label: "Current state",
          data: [
            Math.round(Number(dimensions.goal_clarity ?? 0.5) * 100),
            Math.round(Number(dimensions.self_efficacy ?? 0.5) * 100),
            Math.round(Number(dimensions.motivation ?? 0.5) * 100),
            Math.round(Number(dimensions.resilience ?? 0.5) * 100),
            Math.round(Number(dimensions.well_being ?? 0.5) * 100),
            Math.round((1 - Number(dimensions.stress_load ?? 0.5)) * 100),
          ],
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124, 58, 237, 0.18)",
        },
      ],
    }
  }, [dimensions])

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
              Hi, {user?.full_name || user?.email}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {latestSnapshot
                ? "Dashboard is now reading from your live self-concept state."
                : "Complete onboarding to establish your first state snapshot."}
            </Typography>
          </Box>
        </Stack>

        {onboardingAssignment ? (
          <Box sx={{ mb: 4 }}>
            <PendingQuestionnaireWidget assignment={onboardingAssignment} />
          </Box>
        ) : null}

        {flow?.pending_action === "complete_onboarding" && !onboardingAssignment ? (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Complete onboarding
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Your dashboard is intentionally empty until your baseline questionnaire is completed.
                </Typography>
              </Box>
              <Button variant="contained" onClick={() => navigate({ to: "/questionnaires" })}>
                Open Onboarding
              </Button>
            </Stack>
          </Paper>
        ) : null}

        {flow?.pending_action === "confirm_week_setup" ? (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Confirm your first week
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Your baseline has been mapped. Review the proposed goals before entering the daily loop.
                </Typography>
              </Box>
              <Button variant="contained" onClick={() => navigate({ to: "/week-setup" })}>
                Open Week Setup
              </Button>
            </Stack>
          </Paper>
        ) : null}

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: "bold", mb: 1 }}>
            Alignment over time
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Identity consistency snapshots generated from your onboarding and follow-on state updates.
          </Typography>
          {alignmentSeries.length === 0 ? (
            <Typography color="text.secondary">
              No self-concept history yet. Finish onboarding to populate this chart.
            </Typography>
          ) : (
            <Box sx={{ height: 320 }}>
              <Line
                data={adherenceChart}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: { y: { min: 0, max: 100, ticks: { stepSize: 20 } } },
                }}
              />
            </Box>
          )}
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: "bold", mb: 1 }}>
            Trait trajectory
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Longitudinal self-concept dimensions derived from the current deterministic state.
          </Typography>
          {history.length === 0 ? (
            <Typography color="text.secondary">
              No trajectory data yet. This will populate after your first snapshot is created.
            </Typography>
          ) : (
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
          )}
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: "bold", mb: 1 }}>
            Current state profile
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            The latest self-concept dimensions currently informing the scaffold.
          </Typography>
          {latestSnapshot ? (
            <Box sx={{ height: 320 }}>
              <Radar
                data={radarData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: "bottom" } },
                  scales: { r: { min: 0, max: 100, ticks: { stepSize: 20 } } },
                }}
              />
            </Box>
          ) : (
            <Typography color="text.secondary">
              No current state yet. Complete onboarding to populate your initial profile.
            </Typography>
          )}
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
            <Typography variant="h5" sx={{ fontWeight: "bold" }}>
              Connected goals
            </Typography>
            <Button
              variant="outlined"
              endIcon={<FiArrowRight />}
              onClick={() => navigate({ to: "/value-map" })}
            >
              View Value Map
            </Button>
          </Box>

          {activeGoals.length === 0 ? (
            <Typography color="text.secondary">
              No weekly goals yet. Finish onboarding to initialize your first week.
            </Typography>
          ) : (
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              {activeGoals.slice(0, 4).map((goal) => (
                <Card
                  key={goal.id}
                  sx={{
                    flex: 1,
                    cursor: "pointer",
                    transition: "transform 0.2s, box-shadow 0.2s",
                    "&:hover": {
                      transform: "translateY(-4px)",
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => navigate({ to: "/value-map" })}
                >
                  <CardContent>
                    <Typography variant="h6" sx={{ fontWeight: "bold", mb: 1 }}>
                      {goal.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {goal.description || "No description yet"}
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      Weekly target: {goal.target_value} {goal.target_unit}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Stack>
          )}
        </Paper>
      </Box>
    </Container>
  )
}
