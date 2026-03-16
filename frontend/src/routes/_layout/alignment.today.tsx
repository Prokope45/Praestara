import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  Container,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useMemo, useState } from "react"

import {
  alignmentApi,
  type AlignmentSurfaceCommitment,
  type AlignmentSurfaceResponse,
  type AlignmentTodayRequest,
} from "@/api/alignment"
import { appFlowApi } from "@/api/appFlow"
import { ApiError } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/alignment/today")({
  component: AlignmentToday,
})

const toDateString = (date: Date) => date.toISOString().slice(0, 10)

function AlignmentToday() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  const selectedDate = toDateString(new Date())
  const [commitments, setCommitments] = useState<Record<string, boolean>>({})
  const [completion, setCompletion] = useState<Record<string, boolean>>({})
  const [note, setNote] = useState("")
  const [lastResponse, setLastResponse] = useState<Record<string, unknown> | null>(null)
  const [savedAt, setSavedAt] = useState<string | null>(null)
  const [mode, setMode] = useState<"morning" | "evening">("morning")

  const todayQuery = useQuery({
    queryKey: ["alignment", "today", selectedDate],
    queryFn: () => alignmentApi.getToday(selectedDate),
  })

  const flowQuery = useQuery({
    queryKey: ["app-flow"],
    queryFn: appFlowApi.getFlow,
  })

  useEffect(() => {
    if (!todayQuery.data) return
    const nextCommitments: Record<string, boolean> = {}
    const nextCompletion: Record<string, boolean> = {}
    todayQuery.data.today_commitments.forEach((item) => {
      nextCommitments[item.goal_name] = item.planned_today
      nextCompletion[item.goal_name] = item.completed_today ?? false
    })
    setCommitments(nextCommitments)
    setCompletion(nextCompletion)
    setNote(
      todayQuery.data.text_context.reflection_text
      || todayQuery.data.text_context.projection_text
      || "",
    )
  }, [todayQuery.data])

  const hasReflection = useMemo(() => {
    const surface = todayQuery.data
    if (!surface) return false
    return surface.today_commitments.some((item) => item.completed_today !== null)
  }, [todayQuery.data])

  useEffect(() => {
    setMode(hasReflection ? "evening" : "morning")
  }, [hasReflection])

  const submitMutation = useMutation({
    mutationFn: (payload: AlignmentTodayRequest) => alignmentApi.postToday(payload),
    onSuccess: (response) => {
      showSuccessToast("Alignment recorded")
      setLastResponse(response.decoded_signal ?? null)
      setSavedAt(new Date().toLocaleTimeString())
      queryClient.invalidateQueries({ queryKey: ["alignment", "today"] })
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        handleError(error)
      } else {
        showErrorToast("Unable to record alignment")
      }
    },
  })

  const submit = () => {
    submitMutation.mutate({
      commitments,
      completion: mode === "evening" ? completion : undefined,
      note: note.trim() || undefined,
    })
  }

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Paper sx={{ p: 4, borderRadius: 4 }}>
        <Stack spacing={3}>
          {flowQuery.data?.pending_action === "confirm_week_setup" ? (
            <Alert severity="info">
              Confirm your current week setup before relying on the daily loop.
            </Alert>
          ) : null}
          <Box>
            <Typography variant="h5">Today</Typography>
            <Typography variant="body2" color="text.secondary">
              {mode === "morning" ? "Set intention for today." : "Mark what happened today."}
            </Typography>
          </Box>

          <Stack direction="row" spacing={1}>
            <Chip
              label="Intention"
              color={mode === "morning" ? "primary" : "default"}
              variant={mode === "morning" ? "filled" : "outlined"}
              onClick={() => setMode("morning")}
            />
            <Chip
              label="Completion"
              color={mode === "evening" ? "primary" : "default"}
              variant={mode === "evening" ? "filled" : "outlined"}
              onClick={() => setMode("evening")}
            />
          </Stack>

          <WeekSummary surface={todayQuery.data} />

          <Stack spacing={1.5}>
            <Typography variant="subtitle1">
              {mode === "morning" ? "Today, I will:" : "Today, I completed:"}
            </Typography>
            {(todayQuery.data?.today_commitments ?? []).map((item) => (
              <CommitmentRow
                key={item.goal_name}
                item={item}
                checked={
                  mode === "morning"
                    ? (commitments[item.goal_name] ?? false)
                    : (completion[item.goal_name] ?? false)
                }
                onChange={(checked) => {
                  if (mode === "morning") {
                    setCommitments((current) => ({ ...current, [item.goal_name]: checked }))
                    return
                  }
                  setCompletion((current) => ({ ...current, [item.goal_name]: checked }))
                }}
              />
            ))}
          </Stack>

          <Stack spacing={1}>
            <Typography variant="subtitle1">Describe today (optional)</Typography>
            <TextField
              multiline
              minRows={4}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Write a short note."
            />
            {savedAt && (
              <Typography variant="caption" color="text.secondary">
                Saved at {savedAt}
              </Typography>
            )}
          </Stack>

          {lastResponse && (
            <Paper variant="outlined" sx={{ p: 2, borderRadius: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Decoder output
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {JSON.stringify(lastResponse)}
              </Typography>
            </Paper>
          )}

          <Button
            variant="contained"
            onClick={submit}
            disabled={submitMutation.isPending || todayQuery.isLoading}
          >
            {submitMutation.isPending ? "Saving..." : "Save"}
          </Button>
        </Stack>
      </Paper>
    </Container>
  )
}

function WeekSummary({ surface }: { surface: AlignmentSurfaceResponse | undefined }) {
  if (!surface?.week_summary.length) {
    return null
  }

  return (
    <Stack spacing={1}>
      <Typography variant="subtitle1">This Week</Typography>
      {surface.week_summary.map((item) => (
        <Box key={item.goal_name}>
          <Typography variant="body1">{item.goal_name}</Typography>
          <Typography variant="body2" color="text.secondary">
            {item.completed} of {item.target} complete · {item.days_remaining} days left
          </Typography>
        </Box>
      ))}
    </Stack>
  )
}

function CommitmentRow({
  item,
  checked,
  onChange,
}: {
  item: AlignmentSurfaceCommitment
  checked: boolean
  onChange: (checked: boolean) => void
}) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1,
        py: 0.5,
      }}
    >
      <Checkbox
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        sx={{ p: 0.5 }}
      />
      <Typography variant="body1">{item.goal_name}</Typography>
    </Box>
  )
}
