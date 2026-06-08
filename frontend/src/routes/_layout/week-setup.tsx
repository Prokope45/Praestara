import {
  Alert,
  Box,
  Button,
  Chip,
  Container,
  Grid,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useEffect, useMemo, useState } from "react"

import { appFlowApi } from "@/api/appFlow"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/week-setup")({
  component: WeekSetup,
})

const WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
const DAY_SHORT: Record<string, string> = {
  Monday: "Mon", Tuesday: "Tue", Wednesday: "Wed", Thursday: "Thu",
  Friday: "Fri", Saturday: "Sat", Sunday: "Sun",
}

function WeekSetup() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [scheduleNote, setScheduleNote] = useState("")
  const [reflection, setReflection] = useState("")
  const [goalNotes, setGoalNotes] = useState<Record<string, string>>({})
  const [targetOverrides] = useState<Record<string, number>>({})
  const [selectedDays, setSelectedDays] = useState<Record<string, string[]>>({})
  const [scheduleDays, setScheduleDays] = useState<
    { day: string; available_hours: number; notes?: string | null }[]
  >([])

  // Normalise day names from API to match WEEK_DAYS casing
  const normDay = (d: string) =>
    WEEK_DAYS.find((w) => w.toLowerCase() === d.toLowerCase()) ?? d

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

  const showOnboardingGate =
    flowQuery.isSuccess && !flowQuery.data?.has_baseline && !setupQuery.data

  const proposals = setupQuery.data?.proposed_goals ?? []

  useEffect(() => {
    if (!setupQuery.data?.schedule_days || scheduleDays.length > 0) return
    setScheduleDays(setupQuery.data.schedule_days)
  }, [scheduleDays.length, setupQuery.data?.schedule_days])

  // Seed day bubbles from suggested_days on first load
  useEffect(() => {
    if (!setupQuery.data?.proposed_goals || Object.keys(selectedDays).length > 0) return
    const init: Record<string, string[]> = {}
    for (const p of setupQuery.data.proposed_goals) {
      init[p.goal_id] = (p.suggested_days ?? []).map(normDay)
    }
    setSelectedDays(init)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setupQuery.data?.proposed_goals])

  const submit = () => {
    mutation.mutate({
      goals: proposals.map((proposal) => {
        // day bubbles are the source of truth for target count
        const days = selectedDays[proposal.goal_id]
        const target = days !== undefined
          ? Math.max(1, days.length)
          : (targetOverrides[proposal.goal_id] ?? proposal.target_value)
        return {
          goal_id: proposal.goal_id,
          accepted: true,
          target_value: target,
          intensity_level: proposal.intensity_level,
          note: goalNotes[proposal.goal_id] || undefined,
        }
      }),
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

        {showOnboardingGate ? (
          <Alert severity="info">
            Complete onboarding first. This step depends on your baseline questionnaire.
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
              const days = selectedDays[proposal.goal_id] ?? []
              const sessionCount = Math.max(1, days.length)

              const toggleDay = (day: string) => {
                setSelectedDays((prev) => {
                  const current = prev[proposal.goal_id] ?? []
                  const next = current.includes(day)
                    ? current.filter((d) => d !== day)
                    : [...current, day]
                  return { ...prev, [proposal.goal_id]: next }
                })
              }

              return (
                <Paper key={proposal.goal_id} sx={{ p: 3 }}>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="h6">{proposal.title}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {proposal.rationale}
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Pick your days — {sessionCount} {proposal.target_unit} per week
                      </Typography>
                      <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                        {WEEK_DAYS.map((day) => {
                          const selected = days.includes(day)
                          return (
                            <Chip
                              key={day}
                              label={DAY_SHORT[day]}
                              onClick={() => toggleDay(day)}
                              color={selected ? "primary" : "default"}
                              variant={selected ? "filled" : "outlined"}
                              sx={{ fontWeight: selected ? 700 : 400, minWidth: 48 }}
                            />
                          )
                        })}
                      </Box>
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
