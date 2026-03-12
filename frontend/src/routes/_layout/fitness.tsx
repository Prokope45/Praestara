import {
  Box,
  Button,
  Chip,
  Container,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
  Checkbox,
} from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useMemo, useState } from "react"

import { fitnessApi, type FitnessSessionLogCreate, type FitnessWeekReflection, type WeeklyFitnessPlanPublic } from "@/api/fitness"
import { ApiError } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/fitness")({
  component: Fitness,
})

const toDateString = (date: Date) => date.toISOString().slice(0, 10)

function Fitness() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  const [weekStart, setWeekStart] = useState("")
  const [forceRegen, setForceRegen] = useState(false)
  const [sessionLog, setSessionLog] = useState<FitnessSessionLogCreate>({
    plan_id: "",
    session_definition_id: "",
    session_date: toDateString(new Date()),
    completed: true,
    adherence_flag: "",
    perceived_effort: null,
    energy_level: null,
    duration_minutes: null,
    executed_stress: null,
    notes: "",
    actual_exercises: null,
  })
  const [weekReflection, setWeekReflection] = useState<FitnessWeekReflection>({
    plan_id: "",
    goal_met: true,
    sessions_completed: null,
    reported_energy: null,
    fatigue_flags: [],
    perceived_difficulty: null,
    injury_signals: [],
    recovery_adequacy: null,
  })

  const [exposureFilters, setExposureFilters] = useState({
    start_date: "",
    end_date: "",
    week_id: "",
  })

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

  const exposureQuery = useQuery({
    queryKey: ["fitness", "exposure", exposureFilters],
    queryFn: () =>
      fitnessApi.getExposureEvents({
        start_date: exposureFilters.start_date || undefined,
        end_date: exposureFilters.end_date || undefined,
        week_id: exposureFilters.week_id || undefined,
      }),
  })

  useEffect(() => {
    if (!currentPlanQuery.data) return
    setSessionLog((prev) => ({
      ...prev,
      plan_id: currentPlanQuery.data.id,
    }))
    setWeekReflection((prev) => ({
      ...prev,
      plan_id: currentPlanQuery.data.id,
    }))
  }, [currentPlanQuery.data])

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

  const logMutation = useMutation({
    mutationFn: (payload: FitnessSessionLogCreate) => fitnessApi.logSession(payload),
    onSuccess: () => {
      showSuccessToast("Session logged")
      queryClient.invalidateQueries({ queryKey: ["fitness", "plan", "current"] })
      queryClient.invalidateQueries({ queryKey: ["fitness", "exposure"] })
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        handleError(error)
      } else {
        showErrorToast("Unable to log session")
      }
    },
  })

  const weekReflectionMutation = useMutation({
    mutationFn: (payload: FitnessWeekReflection) => fitnessApi.submitWeekReflection(payload),
    onSuccess: () => {
      showSuccessToast("Week reflection submitted")
      queryClient.invalidateQueries({ queryKey: ["fitness", "plan", "current"] })
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        handleError(error)
      } else {
        showErrorToast("Unable to submit week reflection")
      }
    },
  })

  const planDetails = currentPlanQuery.data as WeeklyFitnessPlanPublic | null

  const domainAllocation = useMemo(() => {
    if (!planDetails) return []
    return Object.entries(planDetails.domain_allocation || {})
  }, [planDetails])

  const stressBudget = useMemo(() => {
    if (!planDetails) return []
    return Object.entries(planDetails.stress_budget || {})
  }, [planDetails])

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Stack spacing={4}>
        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h5">Generate weekly fitness plan</Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Week start (optional)"
                type="date"
                value={weekStart}
                onChange={(event) => setWeekStart(event.target.value)}
                InputLabelProps={{ shrink: true }}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={forceRegen}
                    onChange={(event) => setForceRegen(event.target.checked)}
                  />
                }
                label="Force regenerate"
              />
            </Stack>
            <Button
              variant="contained"
              onClick={() =>
                generateMutation.mutate({
                  week_start: weekStart || undefined,
                  force_regen: forceRegen,
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
            <Typography variant="h5">Current plan</Typography>
            {currentPlanQuery.isLoading ? (
              <Typography variant="body2">Loading plan...</Typography>
            ) : !planDetails ? (
              <Typography variant="body2" color="text.secondary">
                No active plan for this week.
              </Typography>
            ) : (
              <Stack spacing={2}>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                  <Chip label={`Week ${planDetails.week_start} → ${planDetails.week_end}`} />
                  <Chip label={`Target sessions: ${planDetails.target_sessions}`} color="secondary" />
                  <Chip label={`Completed: ${planDetails.completed_sessions}`} />
                  <Chip label={`Status: ${planDetails.status}`} />
                </Stack>
                <Box>
                  <Typography variant="subtitle1">Domain allocation</Typography>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 1, flexWrap: "wrap" }}>
                    {domainAllocation.map(([domain, value]) => (
                      <Chip key={domain} label={`${domain}: ${Number(value).toFixed(2)}`} />
                    ))}
                  </Stack>
                </Box>
                <Box>
                  <Typography variant="subtitle1">Stress budget</Typography>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 1, flexWrap: "wrap" }}>
                    {stressBudget.map(([key, value]) => (
                      <Chip key={key} label={`${key}: ${Number(value).toFixed(2)}`} />
                    ))}
                  </Stack>
                </Box>
                <Box>
                  <Typography variant="subtitle1">Selected exercises</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {JSON.stringify(planDetails.selected_exercises, null, 2)}
                  </Typography>
                </Box>
              </Stack>
            )}
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h5">Log a session</Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Plan id"
                value={sessionLog.plan_id}
                onChange={(event) =>
                  setSessionLog((prev) => ({ ...prev, plan_id: event.target.value }))
                }
                fullWidth
              />
              <TextField
                label="Session definition id (optional)"
                value={sessionLog.session_definition_id ?? ""}
                onChange={(event) =>
                  setSessionLog((prev) => ({
                    ...prev,
                    session_definition_id: event.target.value,
                  }))
                }
                fullWidth
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Session date"
                type="date"
                value={sessionLog.session_date}
                onChange={(event) =>
                  setSessionLog((prev) => ({
                    ...prev,
                    session_date: event.target.value,
                  }))
                }
                InputLabelProps={{ shrink: true }}
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel id="adherence-flag">Adherence</InputLabel>
                <Select
                  labelId="adherence-flag"
                  label="Adherence"
                  value={sessionLog.adherence_flag ?? ""}
                  onChange={(event) =>
                    setSessionLog((prev) => ({
                      ...prev,
                      adherence_flag: String(event.target.value),
                    }))
                  }
                >
                  <MenuItem value="">Auto</MenuItem>
                  <MenuItem value="full">Full</MenuItem>
                  <MenuItem value="partial">Partial</MenuItem>
                  <MenuItem value="skipped">Skipped</MenuItem>
                </Select>
              </FormControl>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={sessionLog.completed}
                    onChange={(event) =>
                      setSessionLog((prev) => ({
                        ...prev,
                        completed: event.target.checked,
                      }))
                    }
                  />
                }
                label="Completed"
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Perceived effort"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                value={sessionLog.perceived_effort ?? ""}
                onChange={(event) =>
                  setSessionLog((prev) => ({
                    ...prev,
                    perceived_effort: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                fullWidth
              />
              <TextField
                label="Energy level"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                value={sessionLog.energy_level ?? ""}
                onChange={(event) =>
                  setSessionLog((prev) => ({
                    ...prev,
                    energy_level: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                fullWidth
              />
              <TextField
                label="Duration (minutes)"
                type="number"
                inputProps={{ min: 1, step: 1 }}
                value={sessionLog.duration_minutes ?? ""}
                onChange={(event) =>
                  setSessionLog((prev) => ({
                    ...prev,
                    duration_minutes: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                fullWidth
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Executed stress"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                value={sessionLog.executed_stress ?? ""}
                onChange={(event) =>
                  setSessionLog((prev) => ({
                    ...prev,
                    executed_stress: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                fullWidth
              />
              <TextField
                label="Notes"
                value={sessionLog.notes ?? ""}
                onChange={(event) =>
                  setSessionLog((prev) => ({
                    ...prev,
                    notes: event.target.value,
                  }))
                }
                fullWidth
              />
            </Stack>
            <Button
              variant="contained"
              onClick={() => {
                if (!sessionLog.plan_id) {
                  showErrorToast("Plan id is required")
                  return
                }
                logMutation.mutate({
                  ...sessionLog,
                  adherence_flag: sessionLog.adherence_flag || null,
                  session_definition_id: sessionLog.session_definition_id || null,
                  notes: sessionLog.notes || null,
                })
              }}
              disabled={logMutation.isPending}
            >
              {logMutation.isPending ? "Logging..." : "Log session"}
            </Button>
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h5">Week reflection</Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Plan id"
                value={weekReflection.plan_id}
                onChange={(event) =>
                  setWeekReflection((prev) => ({
                    ...prev,
                    plan_id: event.target.value,
                  }))
                }
                fullWidth
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={weekReflection.goal_met}
                    onChange={(event) =>
                      setWeekReflection((prev) => ({
                        ...prev,
                        goal_met: event.target.checked,
                      }))
                    }
                  />
                }
                label="Goal met"
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Sessions completed"
                type="number"
                inputProps={{ min: 0, step: 1 }}
                value={weekReflection.sessions_completed ?? ""}
                onChange={(event) =>
                  setWeekReflection((prev) => ({
                    ...prev,
                    sessions_completed: event.target.value
                      ? Number(event.target.value)
                      : null,
                  }))
                }
                fullWidth
              />
              <TextField
                label="Reported energy"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                value={weekReflection.reported_energy ?? ""}
                onChange={(event) =>
                  setWeekReflection((prev) => ({
                    ...prev,
                    reported_energy: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                fullWidth
              />
              <TextField
                label="Perceived difficulty"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                value={weekReflection.perceived_difficulty ?? ""}
                onChange={(event) =>
                  setWeekReflection((prev) => ({
                    ...prev,
                    perceived_difficulty: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                fullWidth
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Recovery adequacy"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                value={weekReflection.recovery_adequacy ?? ""}
                onChange={(event) =>
                  setWeekReflection((prev) => ({
                    ...prev,
                    recovery_adequacy: event.target.value ? Number(event.target.value) : null,
                  }))
                }
                fullWidth
              />
              <TextField
                label="Fatigue flags (comma)"
                value={(weekReflection.fatigue_flags ?? []).join(", ")}
                onChange={(event) =>
                  setWeekReflection((prev) => ({
                    ...prev,
                    fatigue_flags: event.target.value
                      ? event.target.value.split(",").map((flag) => flag.trim()).filter(Boolean)
                      : [],
                  }))
                }
                fullWidth
              />
              <TextField
                label="Injury signals (comma)"
                value={(weekReflection.injury_signals ?? []).join(", ")}
                onChange={(event) =>
                  setWeekReflection((prev) => ({
                    ...prev,
                    injury_signals: event.target.value
                      ? event.target.value.split(",").map((flag) => flag.trim()).filter(Boolean)
                      : [],
                  }))
                }
                fullWidth
              />
            </Stack>
            <Button
              variant="contained"
              onClick={() => {
                if (!weekReflection.plan_id) {
                  showErrorToast("Plan id is required")
                  return
                }
                weekReflectionMutation.mutate(weekReflection)
              }}
              disabled={weekReflectionMutation.isPending}
            >
              {weekReflectionMutation.isPending ? "Submitting..." : "Submit week reflection"}
            </Button>
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h5">Exposure events</Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Start date"
                type="date"
                value={exposureFilters.start_date}
                onChange={(event) =>
                  setExposureFilters((prev) => ({
                    ...prev,
                    start_date: event.target.value,
                  }))
                }
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="End date"
                type="date"
                value={exposureFilters.end_date}
                onChange={(event) =>
                  setExposureFilters((prev) => ({
                    ...prev,
                    end_date: event.target.value,
                  }))
                }
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="Week id"
                value={exposureFilters.week_id}
                onChange={(event) =>
                  setExposureFilters((prev) => ({
                    ...prev,
                    week_id: event.target.value,
                  }))
                }
              />
              <Button variant="outlined" onClick={() => exposureQuery.refetch()}>
                Refresh
              </Button>
            </Stack>
            {exposureQuery.data?.events?.length ? (
              <Stack spacing={2}>
                {exposureQuery.data.events.map((event, idx) => (
                  <Paper key={`${event.week_id}-${idx}`} variant="outlined" sx={{ p: 2 }}>
                    <Stack spacing={1}>
                      <Typography variant="subtitle2">{new Date(event.timestamp).toLocaleString()}</Typography>
                      <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                        <Chip label={`Exposure id: ${event.id}`} />
                        <Chip label={`Week: ${event.week_id}`} />
                        <Chip label={`Adherence: ${event.adherence_flag}`} color="secondary" />
                        <Chip label={`Planned stress: ${event.planned_stress}`} />
                        <Chip label={`Executed stress: ${event.executed_stress ?? "n/a"}`} />
                      </Stack>
                      <Typography variant="body2">
                        Duration: {event.duration_minutes ?? "n/a"} min
                      </Typography>
                      <Typography variant="body2">
                        Domains: {JSON.stringify(event.domain_distribution)}
                      </Typography>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No exposure events found.
              </Typography>
            )}
          </Stack>
        </Paper>
      </Stack>
    </Container>
  )
}
