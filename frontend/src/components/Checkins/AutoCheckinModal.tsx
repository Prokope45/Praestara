import { Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from "@mui/material"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect, useMemo, useState } from "react"

import { CheckinsService, QuestionnairesService } from "@/client"
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
  const [openType, setOpenType] = useState<"morning" | "evening" | null>(null)
  const [text, setText] = useState("")
  const [reply, setReply] = useState<string | null>(null)

  const { data: morningHistory } = useQuery({
    queryKey: ["checkins", "morning", "latest"],
    queryFn: () =>
      QuestionnairesService.readQuestionnaireResponses({ kind: "morning_checkin", limit: 20 }),
  })

  const { data: eveningHistory } = useQuery({
    queryKey: ["checkins", "evening", "latest"],
    queryFn: () =>
      QuestionnairesService.readQuestionnaireResponses({ kind: "evening_checkin", limit: 20 }),
  })

  const morningDone = useMemo(() => {
    return (morningHistory?.data ?? []).some((entry) => isSameDay(entry.created_at))
  }, [morningHistory])

  const eveningDone = useMemo(() => {
    return (eveningHistory?.data ?? []).some((entry) => isSameDay(entry.created_at))
  }, [eveningHistory])

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
        }
      } catch {
        // ignore malformed payloads
      } finally {
        localStorage.removeItem(FORCE_KEY)
      }
    }

    handleTrigger()
    window.addEventListener("praestara_checkin_trigger", handleTrigger)
    return () => window.removeEventListener("praestara_checkin_trigger", handleTrigger)
  }, [openType])

  useEffect(() => {
    if (!user?.onboarding_completed_at) return
    if (openType) return

    const dayKey = getDayKey()
    const dismissedMorning = localStorage.getItem(getDismissKey("morning", dayKey))
    const dismissedEvening = localStorage.getItem(getDismissKey("evening", dayKey))

    if (!morningDone && !dismissedMorning) {
      setOpenType("morning")
      return
    }

    const now = new Date()
    if (now.getHours() >= EVENING_HOUR && !eveningDone && !dismissedEvening) {
      setOpenType("evening")
    }
  }, [eveningDone, morningDone, openType, user])

  const mutation = useMutation({
    mutationFn: (payload: { type: "morning" | "evening"; text: string }) =>
      CheckinsService.createCheckin({ requestBody: payload }),
    onSuccess: (response) => {
      setReply(response.reply)
    },
  })

  const handleClose = () => {
    if (openType) {
      localStorage.setItem(getDismissKey(openType, getDayKey()), "1")
    }
    setOpenType(null)
    setText("")
    setReply(null)
  }

  const handleSubmit = () => {
    if (!openType || !text.trim()) return
    mutation.mutate({ type: openType, text })
  }

  if (!openType) return null

  const isMorning = openType === "morning"

  return (
    <Dialog open fullWidth maxWidth="sm">
      <DialogTitle>
        {isMorning ? "Good morning. Who are you going to be today?" : "Good evening. Who were you today?"}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
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
          disabled={mutation.isPending || !text.trim() || Boolean(reply)}
        >
          {mutation.isPending ? "Submitting..." : "Submit"}
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
