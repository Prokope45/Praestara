import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  FormGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient} from "@tanstack/react-query"
import { useEffect, useMemo, useState } from "react"

import { CheckinsService, TrajectoriesService, type CheckinTrajectoryResponseCreate } from "@/client"
import useAuth from "@/hooks/useAuth"

const isSameDay = (dateString: string) => {
  const candidate = new Date(dateString)
  const today = new Date()
  return candidate.toDateString() === today.toDateString()
}

const getDismissKey = (type: "morning" | "evening", dayKey: string) =>
  `praestara_checkin_dismissed_${type}_${dayKey}`

const getDayKey = () => new Date().toISOString().slice(0, 10)

const EVENING_HOUR = 18
const FORCE_KEY = "praestara_checkin_force"

function AutoCheckinModal() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [openType, setOpenType] = useState<"morning" | "evening" | null>(null)
  const [text, setText] = useState("")
  const [reply, setReply] = useState<string | null>(null)
  const [trajectoryAnswers, setTrajectoryAnswers] = useState<Record<string, boolean>>({})
  const [initialized, setInitialized] = useState(false)

  const { data: morningHistory } = useQuery({
    queryKey: ["checkins", "morning", "latest"],
    queryFn: () => CheckinsService.readCheckins({ type: "morning", limit: 20 }),
  })

  const { data: eveningHistory } = useQuery({
    queryKey: ["checkins", "evening", "latest"],
    queryFn: () => CheckinsService.readCheckins({ type: "evening", limit: 20 }),
  })

  const { data: activeTrajectories } = useQuery({
    queryKey: ["trajectories", "active"],
    queryFn: () => TrajectoriesService.getActiveTrajectories(),
    enabled: !!openType,
  })

  const todayMorningEntry = useMemo(() => {
    return (morningHistory?.data ?? []).find((entry) => isSameDay(entry.created_at))
  }, [morningHistory])

  const todayEveningEntry = useMemo(() => {
    return (eveningHistory?.data ?? []).find((entry) => isSameDay(entry.created_at))
  }, [eveningHistory])

  const morningDone = Boolean(todayMorningEntry)
  const eveningDone = Boolean(todayEveningEntry)
  const currentEntry = openType === "morning" ? todayMorningEntry : todayEveningEntry

  useEffect(() => {
    const handleTrigger = () => {
      if (openType) return
      const raw = localStorage.getItem(FORCE_KEY)
      if (!raw) return
      try {
        const parsed = JSON.parse(raw)
        if (parsed?.type === "morning" || parsed?.type === "evening") {
          setOpenType(parsed.type)
          setText("")
          setReply(null)
          setTrajectoryAnswers({})
        }
      } catch {
        // ignore malformed payloads
      } finally {
        localStorage.removeItem(FORCE_KEY)
      }
    }

    handleTrigger()
    window.addEventListener("praestara_checkin_trigger", handleTrigger)
    return () =>
      window.removeEventListener("praestara_checkin_trigger", handleTrigger)
  }, [openType])

  useEffect(() => {
    // If there's an active trajectory modal, don't show the checkin modal yet
    const rawTrajectoryForce = localStorage.getItem("praestara_trajectory_force")
    if (rawTrajectoryForce === "1") return

    if (openType && !initialized) {
      if (currentEntry) {
        setText(currentEntry.text)
        setReply(currentEntry.reply)
        setInitialized(true)
      } else if (morningHistory && eveningHistory) {
        setText("")
        setReply(null)
        setInitialized(true)
      }
    } else if (!openType) {
      setInitialized(false)
    }
  }, [openType, currentEntry, initialized, morningHistory, eveningHistory])

  useEffect(() => {
    if (!user?.onboarding_completed_at) return
    if (openType) return

    // Do not show checkin modal if trajectory is due
    const now = new Date()
    if (!user.next_trajectory_date) return
    if (now >= new Date(user.next_trajectory_date)) return

    const dayKey = getDayKey()
    const dismissedMorning = localStorage.getItem(
      getDismissKey("morning", dayKey),
    )
    const dismissedEvening = localStorage.getItem(
      getDismissKey("evening", dayKey),
    )

    if (!morningDone && !dismissedMorning) {
      setOpenType("morning")
      return
    }

    if (now.getHours() >= EVENING_HOUR && !eveningDone && !dismissedEvening) {
      setOpenType("evening")
    }
  }, [eveningDone, morningDone, openType, user])

  const createMutation = useMutation({
    mutationFn: (payload: { type: "morning" | "evening"; text: string; trajectory_responses?: CheckinTrajectoryResponseCreate[] }) =>
      CheckinsService.createCheckin({ requestBody: payload }),
    onSuccess: (response) => {
      setReply(response.reply)
      queryClient.invalidateQueries({ queryKey: ["checkins"] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (payload: { checkinId: string; text: string }) =>
      CheckinsService.updateCheckin({
        checkinId: payload.checkinId,
        requestBody: { text: payload.text },
      }),
    onSuccess: (response) => {
      setReply(response.reply)
      queryClient.invalidateQueries({ queryKey: ["checkins"] })
    },
  })

  const handleClose = () => {
    if (openType) {
      localStorage.setItem(getDismissKey(openType, getDayKey()), "1")
    }
    setOpenType(null)
    setText("")
    setReply(null)
    setTrajectoryAnswers({})
  }

  const handleSubmit = () => {
    if (!openType || !text.trim()) return
    
    const responses: CheckinTrajectoryResponseCreate[] = Object.entries(trajectoryAnswers).map(
      ([id, completed]) => ({ trajectory_id: id, completed })
    )
    if (currentEntry) {
      updateMutation.mutate({ checkinId: currentEntry.id, text })
    } else {
      createMutation.mutate({ type: openType, text, trajectory_responses: responses })
    }
  }

  if (!openType) return null

  const isMorning = openType === "morning"
  const trajectories = activeTrajectories?.data ?? []
  const isPending = createMutation.isPending || updateMutation.isPending
  const isTextUnchanged = currentEntry ? text === currentEntry.text : false

  return (
    <Dialog open fullWidth maxWidth="sm">
      <DialogTitle>
        {isMorning
          ? "Good morning. Who are you going to be today?"
          : "Good evening. Who were you today?"}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {trajectories.length > 0 && !reply && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Weekly Trajectories
              </Typography>
              <FormGroup>
                {trajectories.map((t) => (
                  <FormControlLabel
                    key={t.id}
                    control={
                      <Checkbox
                        checked={trajectoryAnswers[t.id] || false}
                        onChange={(e) => setTrajectoryAnswers({ ...trajectoryAnswers, [t.id]: e.target.checked })}
                      />
                    }
                    label={isMorning ? t.rephrased_morning_question || t.original_goal : t.rephrased_evening_question || t.original_goal}
                  />
                ))}
              </FormGroup>
            </Box>
          )}

          <Typography variant="body2" color="text.secondary">
            Describe today.
          </Typography>
          <TextField
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder={isMorning ? "Today I plan to..." : "Today I..."}
            fullWidth
            multiline
            minRows={4}
          />
          {reply && (
            <Box sx={{ p: 2, bgcolor: "grey.100", borderRadius: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Praestara reflection
              </Typography>
              <Typography variant="body2">{reply}</Typography>
            </Box>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button variant="outlined" onClick={handleClose}>
          Dismiss
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={isPending || !text.trim() || (Boolean(reply) && isTextUnchanged)}
        >
          {isPending ? "Submitting..." : (currentEntry ? "Update" : "Submit")}
        </Button>
        {reply && (
          <Button variant="contained" color="success" onClick={handleClose}>
            Continue
          </Button>
        )}
      </DialogActions>
    </Dialog>
  )
}

export default AutoCheckinModal
