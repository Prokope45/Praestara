import {
  Alert,
  Box,
  Button,
  Container,
  Grid,
  Paper,
  Slider,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useEffect, useMemo, useState } from "react"

import { appFlowApi } from "@/api/appFlow"
import { devPresetsApi } from "@/api/devPresets"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/week-setup")({
  component: WeekSetup,
})

function WeekSetup() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [scheduleNote, setScheduleNote] = useState("")
  const [reflection, setReflection] = useState("")
  const [goalNotes, setGoalNotes] = useState<Record<string, string>>({})
  const [targetOverrides, setTargetOverrides] = useState<Record<string, number>>({})
  const [scheduleDays, setScheduleDays] = useState<
    { day: string; available_hours: number; notes?: string | null }[]
  >([])
  const [presetLoading, setPresetLoading] = useState(false)

  const flowQuery = useQuery({
    queryKey: ["app-flow"],
    queryFn: appFlowApi.getFlow,
  })

  const setupQuery = useQuery({
    queryKey: ["week-setup"],
    queryFn: appFlowApi.getWeekSetup,
  })

  const mutation = useMutation({
    mutationFn: appFlowApi.submitWeekSetup,
    onSuccess: () => {
      showSuccessToast("Week setup confirmed")
      queryClient.invalidateQueries({ queryKey: ["app-flow"] })
      queryClient.invalidateQueries({ queryKey: ["week-setup"] })
      queryClient.invalidateQueries({ queryKey: ["alignment", "today"] })
      queryClient.invalidateQueries({ queryKey: ["goal-scaffold", "goals"] })
      navigate({ to: "/alignment/today" })
    },
    onError: () => {
      showErrorToast("Unable to save week setup")
    },
  })

  const canProceed = flowQuery.data?.has_baseline

  const proposals = setupQuery.data?.proposed_goals ?? []

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get("devPreset") !== "week_setup") {
      return
    }

    let active = true
    setPresetLoading(true)
    devPresetsApi.apply("week_setup")
      .then(async () => {
        if (!active) return
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ["app-flow"] }),
          queryClient.invalidateQueries({ queryKey: ["week-setup"] }),
          queryClient.invalidateQueries({ queryKey: ["questionnaire-assignments"] }),
          queryClient.invalidateQueries({ queryKey: ["goal-scaffold", "goals"] }),
          queryClient.invalidateQueries({ queryKey: ["self-concept", "snapshot"] }),
          queryClient.invalidateQueries({ queryKey: ["self-concept", "history"] }),
        ])
        window.history.replaceState({}, "", "/week-setup")
        showSuccessToast("Preset baseline loaded")
      })
      .catch(() => {
        if (!active) return
        showErrorToast("Unable to load preset baseline")
      })
      .finally(() => {
        if (active) {
          setPresetLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [queryClient, showErrorToast, showSuccessToast])

  useEffect(() => {
    if (!setupQuery.data?.schedule_days || scheduleDays.length > 0) {
      return
    }
    setScheduleDays(setupQuery.data.schedule_days)
  }, [scheduleDays.length, setupQuery.data?.schedule_days])

  const submit = () => {
    mutation.mutate({
      goals: proposals.map((proposal) => ({
        goal_id: proposal.goal_id,
        accepted: true,
        target_value: targetOverrides[proposal.goal_id] ?? proposal.target_value,
        intensity_level: proposal.intensity_level,
        note: goalNotes[proposal.goal_id] || undefined,
      })),
      schedule_days: scheduleDays,
      schedule_note: scheduleNote || undefined,
      reflection: reflection || undefined,
    })
  }

  const phaseLabel = useMemo(() => {
    return (setupQuery.data?.current_phase ?? flowQuery.data?.current_phase ?? "baseline_pending")
      .split("_")
      .join(" ")
  }, [flowQuery.data?.current_phase, setupQuery.data?.current_phase])

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Week Setup
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Confirm the proposed goals for week one and adjust them until they fit your schedule.
          </Typography>
        </Box>

        {!canProceed ? (
          <Alert severity="info">
            Complete onboarding first. This step depends on your baseline questionnaire.
          </Alert>
        ) : null}
        {presetLoading ? (
          <Alert severity="info">
            Loading preset baseline for week setup...
          </Alert>
        ) : null}

        {setupQuery.data ? (
          <>
            <Paper sx={{ p: 3 }}>
              <Stack spacing={1}>
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  Current phase
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {phaseLabel}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {setupQuery.data.narrative_prompt}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Weekly availability: {setupQuery.data.weekly_available_hours} hours
                </Typography>
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="h6">Average Week</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Fill in the hours that are realistically open for training, meal prep, sleep setup,
                    or other health practices before you confirm the goals.
                  </Typography>
                </Box>
                <Grid container spacing={2}>
                  {scheduleDays.map((scheduleDay, index) => (
                    <Grid key={scheduleDay.day} size={{ xs: 12, md: 6 }}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Stack spacing={2}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                            {scheduleDay.day}
                          </Typography>
                          <TextField
                            type="number"
                            label="Open hours"
                            value={scheduleDay.available_hours}
                            onChange={(event) =>
                              setScheduleDays((current) =>
                                current.map((item, itemIndex) =>
                                  itemIndex === index
                                    ? {
                                        ...item,
                                        available_hours: Number(event.target.value || 0),
                                      }
                                    : item,
                                ),
                              )
                            }
                            inputProps={{ min: 0, max: 16, step: 0.5 }}
                          />
                          <TextField
                            label="Fixed commitments / useful windows"
                            multiline
                            minRows={2}
                            value={scheduleDay.notes ?? ""}
                            onChange={(event) =>
                              setScheduleDays((current) =>
                                current.map((item, itemIndex) =>
                                  itemIndex === index
                                    ? {
                                        ...item,
                                        notes: event.target.value,
                                      }
                                    : item,
                                ),
                              )
                            }
                            placeholder="Work, school, care, commute, or likely workout / meal-prep windows"
                          />
                        </Stack>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </Stack>
            </Paper>

            {proposals.map((proposal) => {
              const currentTarget = targetOverrides[proposal.goal_id] ?? proposal.target_value
              return (
                <Paper key={proposal.goal_id} sx={{ p: 3 }}>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="h6">{proposal.title}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {proposal.rationale}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Suggested days: {proposal.suggested_days.join(", ")}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Confidence signal: {Math.round(proposal.confidence_signal * 100)} / 100
                    </Typography>
                    <Box>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Target: {currentTarget} {proposal.target_unit}
                      </Typography>
                      <Slider
                        value={currentTarget}
                        min={1}
                        max={7}
                        step={1}
                        marks
                        valueLabelDisplay="auto"
                        onChange={(_, value) =>
                          setTargetOverrides((current) => ({
                            ...current,
                            [proposal.goal_id]: value as number,
                          }))
                        }
                      />
                    </Box>
                    <TextField
                      label="History / friction / context"
                      multiline
                      minRows={2}
                      value={goalNotes[proposal.goal_id] ?? ""}
                      onChange={(event) =>
                        setGoalNotes((current) => ({
                          ...current,
                          [proposal.goal_id]: event.target.value,
                        }))
                      }
                    />
                  </Stack>
                </Paper>
              )
            })}

            <Paper sx={{ p: 3 }}>
              <Stack spacing={2}>
                <TextField
                  label="Schedule fit"
                  multiline
                  minRows={2}
                  value={scheduleNote}
                  onChange={(event) => setScheduleNote(event.target.value)}
                  placeholder="Anything the calendar still misses, including meal prep, bedtime routines, or travel"
                />
                <TextField
                  label="Reflection on the plan"
                  multiline
                  minRows={3}
                  value={reflection}
                  onChange={(event) => setReflection(event.target.value)}
                  placeholder="How does this plan fit your history with these habits?"
                />
                <Button variant="contained" onClick={submit} disabled={mutation.isPending}>
                  {mutation.isPending ? "Saving..." : "Confirm Week"}
                </Button>
              </Stack>
            </Paper>
          </>
        ) : null}
      </Stack>
    </Container>
  )
}
