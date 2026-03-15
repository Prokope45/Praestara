import {
  Box,
  Button,
  Chip,
  Container,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import { fitnessApi, type WeeklyFitnessPlanPublic } from "@/api/fitness"
import { ApiError } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/fitness")({
  component: Fitness,
})

const workoutModes = [
  {
    key: "planned",
    title: "Planned session",
    description: "Use the session the engine built for today.",
  },
  {
    key: "short",
    title: "Short session",
    description: "Keep the session brief and preserve momentum.",
  },
  {
    key: "recovery",
    title: "Recovery",
    description: "Bias toward recovery work.",
  },
  {
    key: "skip",
    title: "Skip",
    description: "Do not train today.",
  },
] as const

type WorkoutMode = (typeof workoutModes)[number]["key"]

function Fitness() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  const [weekStart, setWeekStart] = useState("")
  const [selectedMode, setSelectedMode] = useState<WorkoutMode | null>(null)
  const [sessionSummary, setSessionSummary] = useState<{
    title: string
    duration: string
    movements: string
    sets: string
  } | null>(null)

  const currentPlanQuery = useQuery({
    queryKey: ["fitness", "plan", "current"],
    queryFn: async () => {
      try {
        return await fitnessApi.getCurrentPlan()
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null
        }
        throw error
      }
    },
    retry: false,
  })

  const generateMutation = useMutation({
    mutationFn: (payload: { week_start?: string | null; force_regen?: boolean }) =>
      fitnessApi.generatePlan(payload),
    onSuccess: () => {
      showSuccessToast("Weekly plan generated")
      queryClient.invalidateQueries({ queryKey: ["fitness", "plan", "current"] })
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        handleError(error)
      } else {
        showErrorToast("Unable to generate plan")
      }
    },
  })

  const planDetails = currentPlanQuery.data as WeeklyFitnessPlanPublic | null

  useEffect(() => {
    if (!planDetails) {
      setSessionSummary(null)
      return
    }

    const outlines = Array.isArray(planDetails.session_outlines)
      ? planDetails.session_outlines
      : []
    const session = outlines[0] as Record<string, unknown> | undefined
    const exercises = Array.isArray(session?.exercises) ? session.exercises : []
    const selectedExercises = Array.isArray(planDetails.selected_exercises)
      ? planDetails.selected_exercises
      : []
    const movementCount = Math.max(exercises.length, selectedExercises.length, 2)
    const sets = exercises.reduce((total, exercise) => {
      const typedExercise = exercise as Record<string, unknown>
      return total + (typeof typedExercise.sets === "number" ? typedExercise.sets : 0)
    }, 0)
    const duration = typeof session?.duration_minutes === "number"
      ? `${session.duration_minutes} minutes`
      : "20 minutes"

    setSessionSummary({
      title: "Lift session",
      duration,
      movements: `${movementCount} movements`,
      sets: `${Math.max(sets, 6)} total sets`,
    })
  }, [planDetails])

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Stack spacing={3}>
        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h5">Workout</Typography>
            <Typography variant="body2" color="text.secondary">
              Generate this week&apos;s plan, then pick the shape of today&apos;s session.
            </Typography>
            <TextField
              label="Week start (optional)"
              type="date"
              value={weekStart}
              onChange={(event) => setWeekStart(event.target.value)}
              InputLabelProps={{ shrink: true }}
            />
            <Button
              variant="contained"
              onClick={() =>
                generateMutation.mutate({
                  week_start: weekStart || undefined,
                  force_regen: false,
                })
              }
              disabled={generateMutation.isPending}
            >
              {generateMutation.isPending ? "Generating..." : "Generate plan"}
            </Button>
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h5">What kind of workout?</Typography>
            {currentPlanQuery.isLoading ? (
              <Typography variant="body2">Loading plan...</Typography>
            ) : !planDetails ? (
              <Typography variant="body2" color="text.secondary">
                No active plan for this week.
              </Typography>
            ) : (
              <>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1} flexWrap="wrap">
                  {workoutModes.map((mode) => (
                    <Chip
                      key={mode.key}
                      label={mode.title}
                      color={selectedMode === mode.key ? "primary" : "default"}
                      variant={selectedMode === mode.key ? "filled" : "outlined"}
                      onClick={() => setSelectedMode(mode.key)}
                    />
                  ))}
                </Stack>

                {selectedMode && (
                  <Paper variant="outlined" sx={{ p: 2.5, borderRadius: 3 }}>
                    <Stack spacing={1}>
                      <Typography variant="subtitle1">
                        {workoutModes.find((mode) => mode.key === selectedMode)?.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {workoutModes.find((mode) => mode.key === selectedMode)?.description}
                      </Typography>
                      {selectedMode === "skip" ? (
                        <Typography variant="body1">Skip today.</Typography>
                      ) : (
                        <Box>
                          <Typography variant="body1">{sessionSummary?.title ?? "Lift session"}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {sessionSummary?.duration ?? "20 minutes"}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {sessionSummary?.movements ?? "2 movements"}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {sessionSummary?.sets ?? "6 total sets"}
                          </Typography>
                        </Box>
                      )}
                    </Stack>
                  </Paper>
                )}
              </>
            )}
          </Stack>
        </Paper>
      </Stack>
    </Container>
  )
}
