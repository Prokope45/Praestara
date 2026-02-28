import {
  Box,
  Button,
  Checkbox,
  Chip,
  Container,
  Divider,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect, useMemo, useState } from "react"

import { alignmentApi, type AlignmentCompletion, type AlignmentDailyRequest } from "@/api/alignment"
import { ApiError } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/alignment")({
  component: Alignment,
})

const toDateString = (date: Date) => date.toISOString().slice(0, 10)

const startOfWeek = (date: Date) => {
  const d = new Date(date)
  const day = d.getDay()
  const diff = (day + 6) % 7
  d.setDate(d.getDate() - diff)
  return d
}

type FitnessContextState = {
  exposure_event_id: string
  adherence_flag: string
  executed_stress: string
  friction_reason: string
  constraint_mismatch_flag: boolean
  perceived_alignment_score: string
}

function Alignment() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [selectedDate, setSelectedDate] = useState(() => toDateString(new Date()))
  const [weekStart, setWeekStart] = useState(() => toDateString(startOfWeek(new Date())))
  const [completionMap, setCompletionMap] = useState<Record<string, boolean>>({})
  const [fitnessContext, setFitnessContext] = useState<FitnessContextState>({
    exposure_event_id: "",
    adherence_flag: "",
    executed_stress: "",
    friction_reason: "",
    constraint_mismatch_flag: false,
    perceived_alignment_score: "",
  })

  const [adjustments, setAdjustments] = useState<Record<string, { target_sessions: string; priority_shift: string; constraint_updates: string }>>({
    fitness: { target_sessions: "", priority_shift: "", constraint_updates: "" },
    nutrition: { target_sessions: "", priority_shift: "", constraint_updates: "" },
    sleep: { target_sessions: "", priority_shift: "", constraint_updates: "" },
    other: { target_sessions: "", priority_shift: "", constraint_updates: "" },
  })

  const dailyQuery = useQuery({
    queryKey: ["alignment", "daily", selectedDate],
    queryFn: () => alignmentApi.getDaily(selectedDate),
  })

  const weeklySummaryQuery = useQuery({
    queryKey: ["alignment", "weekly-summary", weekStart],
    queryFn: () => alignmentApi.getWeeklySummary(weekStart),
    enabled: Boolean(weekStart),
  })

  const historyQuery = useQuery({
    queryKey: ["alignment", "history"],
    queryFn: () => alignmentApi.getHistory(),
  })

  useEffect(() => {
    if (!dailyQuery.data) return
    const initial: Record<string, boolean> = {}
    for (const commitment of dailyQuery.data.commitments) {
      initial[`${commitment.module}:${commitment.commitment_id}`] = false
    }
    setCompletionMap(initial)
  }, [dailyQuery.data])

  const dailyMutation = useMutation({
    mutationFn: (payload: AlignmentDailyRequest) => alignmentApi.postDaily(payload),
    onSuccess: () => {
      showSuccessToast("Daily reflection recorded")
      historyQuery.refetch()
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        handleError(error)
      } else {
        showErrorToast("Unable to submit daily reflection")
      }
    },
  })

  const weeklyMeetingMutation = useMutation({
    mutationFn: (payload: { week_start: string; adjustments: any[] }) =>
      alignmentApi.postWeeklyMeeting(payload),
    onSuccess: () => {
      showSuccessToast("Weekly meeting recorded")
      weeklySummaryQuery.refetch()
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        handleError(error)
      } else {
        showErrorToast("Unable to submit weekly meeting")
      }
    },
  })

  const commitments = dailyQuery.data?.commitments ?? []

  const dailyCompletionPayload = useMemo((): AlignmentCompletion[] => {
    return commitments.map((commitment) => {
      const key = `${commitment.module}:${commitment.commitment_id}`
      let context: Record<string, unknown> | undefined
      if (commitment.module === "fitness") {
        context = {
          exposure_event_id: fitnessContext.exposure_event_id || undefined,
          adherence_flag: fitnessContext.adherence_flag || undefined,
          executed_stress: fitnessContext.executed_stress
            ? Number(fitnessContext.executed_stress)
            : undefined,
          friction_reason: fitnessContext.friction_reason || undefined,
          constraint_mismatch_flag: fitnessContext.constraint_mismatch_flag,
          perceived_alignment_score: fitnessContext.perceived_alignment_score
            ? Number(fitnessContext.perceived_alignment_score)
            : undefined,
        }
      }
      return {
        module: commitment.module,
        commitment_id: commitment.commitment_id,
        completed: completionMap[key] ?? false,
        context,
      }
    })
  }, [commitments, completionMap, fitnessContext])

  const handleSubmitDaily = () => {
    dailyMutation.mutate({
      date: selectedDate,
      commitments_completed: dailyCompletionPayload,
    })
  }

  const handleSubmitWeekly = () => {
    const entries: any[] = []
    for (const [module, values] of Object.entries(adjustments)) {
      const targetSessions = values.target_sessions.trim()
        ? Number(values.target_sessions)
        : undefined
      const priorityShift = values.priority_shift.trim() || undefined
      let constraintUpdates: Record<string, unknown> | undefined
      if (values.constraint_updates.trim()) {
        try {
          constraintUpdates = JSON.parse(values.constraint_updates)
        } catch (error) {
          showErrorToast(`Invalid JSON for ${module} constraint updates`)
          return
        }
      }
      if (targetSessions === undefined && !priorityShift && !constraintUpdates) {
        continue
      }
      entries.push({
        module,
        target_sessions: targetSessions,
        priority_shift: priorityShift,
        constraint_updates: constraintUpdates,
      })
    }

    if (entries.length === 0) {
      showErrorToast("Add at least one adjustment before submitting.")
      return
    }

    weeklyMeetingMutation.mutate({
      week_start: weekStart,
      adjustments: entries,
    })
  }

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Stack spacing={4}>
        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Box>
              <Typography variant="h5">Daily alignment</Typography>
              <Typography variant="body2" color="text.secondary">
                Review today&apos;s commitments and mark completion.
              </Typography>
            </Box>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems="center">
              <TextField
                label="Date"
                type="date"
                value={selectedDate}
                onChange={(event) => setSelectedDate(event.target.value)}
                InputLabelProps={{ shrink: true }}
              />
              <Button variant="outlined" onClick={() => dailyQuery.refetch()}>
                Refresh
              </Button>
            </Stack>
            <Divider />
            {dailyQuery.isLoading ? (
              <Typography variant="body2">Loading commitments...</Typography>
            ) : commitments.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No commitments available for this day.
              </Typography>
            ) : (
              <Stack spacing={1}>
                {commitments.map((commitment) => {
                  const key = `${commitment.module}:${commitment.commitment_id}`
                  return (
                    <Box
                      key={key}
                      sx={{
                        display: "flex",
                        flexDirection: { xs: "column", sm: "row" },
                        justifyContent: "space-between",
                        alignItems: { sm: "center" },
                        gap: 1,
                        p: 1,
                        borderRadius: 2,
                        bgcolor: "background.default",
                      }}
                    >
                      <Box>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Chip size="small" label={commitment.module} color="secondary" />
                          <Typography variant="subtitle1">{commitment.label}</Typography>
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                          {commitment.commitment_id}
                        </Typography>
                      </Box>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={completionMap[key] ?? false}
                            onChange={(event) =>
                              setCompletionMap((prev) => ({
                                ...prev,
                                [key]: event.target.checked,
                              }))
                            }
                          />
                        }
                        label="Completed"
                      />
                    </Box>
                  )
                })}
              </Stack>
            )}
            <Divider />
            <Typography variant="subtitle1">Fitness reflection context (optional)</Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Exposure event id"
                value={fitnessContext.exposure_event_id}
                onChange={(event) =>
                  setFitnessContext((prev) => ({
                    ...prev,
                    exposure_event_id: event.target.value,
                  }))
                }
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel id="adherence-flag-label">Adherence flag</InputLabel>
                <Select
                  labelId="adherence-flag-label"
                  label="Adherence flag"
                  value={fitnessContext.adherence_flag}
                  onChange={(event) =>
                    setFitnessContext((prev) => ({
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
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Executed stress"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                value={fitnessContext.executed_stress}
                onChange={(event) =>
                  setFitnessContext((prev) => ({
                    ...prev,
                    executed_stress: event.target.value,
                  }))
                }
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel id="friction-reason-label">Friction reason</InputLabel>
                <Select
                  labelId="friction-reason-label"
                  label="Friction reason"
                  value={fitnessContext.friction_reason}
                  onChange={(event) =>
                    setFitnessContext((prev) => ({
                      ...prev,
                      friction_reason: String(event.target.value),
                    }))
                  }
                >
                  <MenuItem value="">None</MenuItem>
                  <MenuItem value="time_constraint">Time constraint</MenuItem>
                  <MenuItem value="energy_low">Energy low</MenuItem>
                  <MenuItem value="resource_gap">Resource gap</MenuItem>
                  <MenuItem value="motivation_low">Motivation low</MenuItem>
                  <MenuItem value="injury">Injury</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={fitnessContext.constraint_mismatch_flag}
                    onChange={(event) =>
                      setFitnessContext((prev) => ({
                        ...prev,
                        constraint_mismatch_flag: event.target.checked,
                      }))
                    }
                  />
                }
                label="Constraint mismatch"
              />
              <TextField
                label="Perceived alignment score"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                value={fitnessContext.perceived_alignment_score}
                onChange={(event) =>
                  setFitnessContext((prev) => ({
                    ...prev,
                    perceived_alignment_score: event.target.value,
                  }))
                }
                fullWidth
              />
            </Stack>
            <Button
              variant="contained"
              onClick={handleSubmitDaily}
              disabled={dailyMutation.isPending || commitments.length === 0}
            >
              {dailyMutation.isPending ? "Submitting..." : "Submit daily reflection"}
            </Button>
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Box>
              <Typography variant="h5">Weekly summary</Typography>
              <Typography variant="body2" color="text.secondary">
                Module signals for the selected week start.
              </Typography>
            </Box>
            <TextField
              label="Week start"
              type="date"
              value={weekStart}
              onChange={(event) => setWeekStart(event.target.value)}
              InputLabelProps={{ shrink: true }}
            />
            {weeklySummaryQuery.data?.summaries && (
              <Stack spacing={2}>
                {weeklySummaryQuery.data.summaries.map((summary) => (
                  <Paper key={summary.module} variant="outlined" sx={{ p: 2 }}>
                    <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="center">
                      <Chip label={summary.module} color="secondary" />
                      <Typography variant="body2">
                        Adherence: {(summary.adherence_rate * 100).toFixed(0)}%
                      </Typography>
                      <Typography variant="body2">
                        Burnout: {summary.burnout_index ?? "n/a"}
                      </Typography>
                      <Typography variant="body2">
                        Exposure: {summary.exposure_density}
                      </Typography>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            )}
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Box>
              <Typography variant="h5">Weekly meeting</Typography>
              <Typography variant="body2" color="text.secondary">
                Record constraint shifts and target adjustments.
              </Typography>
            </Box>
            <Stack spacing={2}>
              {Object.keys(adjustments).map((module) => (
                <Paper key={module} variant="outlined" sx={{ p: 2 }}>
                  <Stack spacing={2}>
                    <Typography variant="subtitle1" sx={{ textTransform: "capitalize" }}>
                      {module}
                    </Typography>
                    <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                      <TextField
                        label="Target sessions"
                        type="number"
                        value={adjustments[module].target_sessions}
                        onChange={(event) =>
                          setAdjustments((prev) => ({
                            ...prev,
                            [module]: {
                              ...prev[module],
                              target_sessions: event.target.value,
                            },
                          }))
                        }
                        fullWidth
                      />
                      <TextField
                        label="Priority shift"
                        value={adjustments[module].priority_shift}
                        onChange={(event) =>
                          setAdjustments((prev) => ({
                            ...prev,
                            [module]: {
                              ...prev[module],
                              priority_shift: event.target.value,
                            },
                          }))
                        }
                        fullWidth
                      />
                    </Stack>
                    <TextField
                      label="Constraint updates (JSON)"
                      value={adjustments[module].constraint_updates}
                      onChange={(event) =>
                        setAdjustments((prev) => ({
                          ...prev,
                          [module]: {
                            ...prev[module],
                            constraint_updates: event.target.value,
                          },
                        }))
                      }
                      placeholder='{"time_budget": 120}'
                      fullWidth
                      multiline
                      minRows={2}
                    />
                  </Stack>
                </Paper>
              ))}
            </Stack>
            <Button
              variant="contained"
              onClick={handleSubmitWeekly}
              disabled={weeklyMeetingMutation.isPending}
            >
              {weeklyMeetingMutation.isPending ? "Submitting..." : "Submit weekly meeting"}
            </Button>
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Box>
              <Typography variant="h5">Alignment history</Typography>
              <Typography variant="body2" color="text.secondary">
                Projection → reflection arc with exposure links.
              </Typography>
            </Box>
            {historyQuery.data?.timeline?.length ? (
              <Stack spacing={2}>
                {historyQuery.data.timeline.map((entry) => (
                  <Paper key={entry.date} variant="outlined" sx={{ p: 2 }}>
                    <Stack spacing={1}>
                      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                        <Typography variant="subtitle1">{entry.date}</Typography>
                        <Chip
                          label={entry.reflection_status}
                          color={entry.reflection_status === "completed" ? "success" : "warning"}
                        />
                      </Stack>
                      <Typography variant="body2">
                        Commitments: {entry.commitments.join(", ") || "None"}
                      </Typography>
                      <Typography variant="body2">
                        Modules: {entry.modules_affected.join(", ") || "None"}
                      </Typography>
                      <Typography variant="body2">
                        Exposure links: {entry.exposure_links.join(", ") || "None"}
                      </Typography>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No alignment history yet.
              </Typography>
            )}
          </Stack>
        </Paper>
      </Stack>
    </Container>
  )
}
