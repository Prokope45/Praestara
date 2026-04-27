import {
  Box,
  Checkbox,
  CircularProgress,
  LinearProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  FormGroup,
  IconButton,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient} from "@tanstack/react-query"
import { useEffect, useMemo, useRef, useState } from "react"
import { FiSend, FiX } from "react-icons/fi"
import { WiSunrise } from "react-icons/wi";
import { WiSunset } from "react-icons/wi";

import { CheckinsService, TrajectoriesService, type CheckinTrajectoryResponseCreate } from "@/client"
import useAuth from "@/hooks/useAuth"

type CheckinConversationMessage = {
  role: "user" | "assistant" | "prompt"
  text: string
}

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
  const [messages, setMessages] = useState<CheckinConversationMessage[]>([])
  const [pendingUserText, setPendingUserText] = useState("")
  const [trajectoryAnswers, setTrajectoryAnswers] = useState<Record<string, boolean>>({})
  const [initialized, setInitialized] = useState(false)
  const conversationRef = useRef<HTMLDivElement | null>(null)

  const parseConversation = (
    rawReply: string | null | undefined,
    userText: string,
    apiMessages?: CheckinConversationMessage[],
  ): { reply: string | null; messages: CheckinConversationMessage[] } => {
    if (apiMessages?.length) {
      return { reply: rawReply ?? null, messages: apiMessages }
    }

    if (!rawReply) {
      return {
        reply: null,
        messages: userText.trim() ? [{ role: "user", text: userText.trim() }] : [],
      }
    }

    try {
      const payload = JSON.parse(rawReply)
      if (Array.isArray(payload?.messages)) {
        return {
          reply: typeof payload?.reply === "string" ? payload.reply : rawReply,
          messages: payload.messages as CheckinConversationMessage[],
        }
      }
    } catch {
      // fall through to legacy formatting
    }

    return {
      reply: rawReply,
      messages: [
        ...(userText.trim() ? [{ role: "user" as const, text: userText.trim() }] : []),
        ...rawReply
          .split(/\n{2,}/)
          .map((chunk) => chunk.trim())
          .filter(Boolean)
          .map((chunk) => ({ role: "assistant" as const, text: chunk })),
      ],
    }
  }

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
  const trajectories = activeTrajectories?.data ?? []

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
          setPendingUserText("")
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
        setMessages(
          parseConversation(
            currentEntry.reply,
            currentEntry.text,
            (currentEntry as unknown as { messages?: CheckinConversationMessage[] }).messages,
          ).messages,
        )
        setInitialized(true)
      } else if (morningHistory && eveningHistory) {
        setText("")
        setReply(null)
        setPendingUserText("")
        setMessages([])
        setInitialized(true)
      }
    } else if (!openType) {
      setInitialized(false)
    }
  }, [openType, currentEntry, initialized, morningHistory, eveningHistory])

  useEffect(() => {
    if (openType) return

    // Do not show checkin modal if trajectory is due
    const now = new Date()
    if (user?.next_trajectory_date && now >= new Date(user.next_trajectory_date)) return

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
    mutationFn: (payload: {
      type: "morning" | "evening"
      text: string
      trajectory_responses?: CheckinTrajectoryResponseCreate[]
      messages?: CheckinConversationMessage[]
    }) =>
      CheckinsService.createCheckin({ requestBody: payload }),
    onSuccess: (response) => {
      setReply(response.reply)
      const parsed = parseConversation(
        response.reply,
        pendingUserText,
        (response as unknown as { messages?: CheckinConversationMessage[] }).messages,
      ).messages
      setMessages(parsed)
      setPendingUserText("")
      queryClient.invalidateQueries({ queryKey: ["checkins"] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (payload: { checkinId: string; text: string; messages?: CheckinConversationMessage[] }) =>
      CheckinsService.updateCheckin({
        checkinId: payload.checkinId,
        requestBody: { text: payload.text, messages: payload.messages },
      }),
    onSuccess: (response) => {
      setReply(response.reply)
      const parsed = parseConversation(
        response.reply,
        pendingUserText,
        (response as unknown as { messages?: CheckinConversationMessage[] }).messages,
      ).messages
      setMessages(parsed)
      setPendingUserText("")
      queryClient.invalidateQueries({ queryKey: ["checkins"] })
    },
  })

  const isPending = createMutation.isPending || updateMutation.isPending

  useEffect(() => {
    const node = conversationRef.current
    if (!node) return
    node.scrollTop = node.scrollHeight
  }, [messages, isPending])

  const handleClose = () => {
    if (openType) {
      localStorage.setItem(getDismissKey(openType, getDayKey()), "1")
    }
    setOpenType(null)
    setText("")
    setReply(null)
    setPendingUserText("")
    setMessages([])
    setTrajectoryAnswers({})
  }

  const handleSubmit = () => {
    if (!openType || !text.trim()) return
    const submittedText = text.trim()
    const nextMessages = [...messages, { role: "user" as const, text: submittedText }]
    setPendingUserText(submittedText)
    setMessages(nextMessages)
    setReply(null)
    setText("")
    
    const responses: CheckinTrajectoryResponseCreate[] = Object.entries(trajectoryAnswers).map(
      ([id, completed]) => ({ trajectory_id: id, completed })
    )
    if (currentEntry) {
      updateMutation.mutate({
        checkinId: currentEntry.id,
        text: submittedText,
        messages: nextMessages,
      })
    } else {
      createMutation.mutate({
        type: openType,
        text: submittedText,
        trajectory_responses: responses,
        messages: nextMessages,
      })
    }
  }

  if (!openType) return null

  const isMorning = openType === "morning"
  return (
    <Dialog
      open
      fullWidth
      maxWidth="sm"
      PaperProps={{
        sx: {
          height: "100dvh",
          maxHeight: "100dvh",
          m: 0,
          borderRadius: 0,
          display: "flex",
        },
      }}
    >
      <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2 }}>
        {isMorning
          ?
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <WiSunrise size={36} color="#FF8C00" />
              Good morning. Who are you going to be today?
            </Box>
          :
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <WiSunset size={36} color="#4B0082" />
              Good evening. Who were you today?
            </Box>
        }
        <IconButton onClick={handleClose} size="small">
          <FiX />
        </IconButton>
      </DialogTitle>
      <DialogContent
        sx={{
          display: "flex",
          flexDirection: "column",
          flex: 1,
          minHeight: 0,
          pt: 2,
        }}
      >
        {trajectories.length > 0 && !reply && (
          <Box sx={{ mb: 2 }}>
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

        <Box
          ref={conversationRef}
          sx={{
            borderRadius: 3,
            border: messages.length > 0 || isPending ? "1px solid" : "none",
            borderColor: "divider",
            bgcolor: messages.length > 0 || isPending ? "#fafafa" : "transparent",
            p: messages.length > 0 || isPending ? 2 : 0,
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            justifyContent: messages.length > 0 || isPending ? "flex-start" : "flex-end",
          }}
        >
          {(messages.length > 0 || isPending) && (
            <>
              <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                Praestara conversation
              </Typography>
              <Stack spacing={1.25}>
                {messages.map((message, index) => (
                  <Box
                    key={`${message.role}-${index}`}
                    sx={{
                      alignSelf: message.role === "user" ? "flex-end" : "flex-start",
                      maxWidth: "88%",
                      px: 1.5,
                      py: 1.1,
                      borderRadius: 2.5,
                      bgcolor:
                        message.role === "user"
                          ? "primary.main"
                          : message.role === "prompt"
                            ? "secondary.light"
                            : "grey.200",
                      color:
                        message.role === "user"
                          ? "primary.contrastText"
                          : "text.primary",
                      border:
                        message.role === "prompt"
                          ? "1px solid rgba(124, 58, 237, 0.22)"
                          : "none",
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{
                        display: "block",
                        mb: 0.5,
                        fontWeight: 700,
                        opacity: 0.72,
                      }}
                    >
                      {message.role === "user"
                        ? "You"
                        : message.role === "prompt"
                          ? "Prompt"
                          : "Praestara"}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        whiteSpace: "pre-wrap",
                        fontStyle: message.role === "prompt" ? "italic" : "normal",
                      }}
                    >
                      {message.text}
                    </Typography>
                  </Box>
                ))}
                {isPending && (
                  <Box
                    sx={{
                      alignSelf: "flex-start",
                      width: "100%",
                      px: 1.5,
                      py: 1.25,
                      borderRadius: 2.5,
                      bgcolor: "rgba(245, 245, 245, 0.95)",
                      border: "1px solid",
                      borderColor: "divider",
                    }}
                  >
                    <Stack spacing={1}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <CircularProgress size={16} />
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Praestara is working on this...
                        </Typography>
                      </Box>
                      <LinearProgress />
                    </Stack>
                  </Box>
                )}
              </Stack>
            </>
          )}
        </Box>

        <Box
          sx={{
            pt: 1.5,
            pb: 1,
            borderTop: "1px solid",
            borderColor: "divider",
            bgcolor: "background.paper",
            display: "flex",
            alignItems: "flex-end",
            gap: 1,
          }}
        >
          <TextField
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault()
                handleSubmit()
              }
            }}
            placeholder={isMorning ? "Today I plan to..." : "Today I..."}
            fullWidth
            multiline
            minRows={1}
            maxRows={4}
            size="small"
            disabled={isPending}
            sx={{
              "& .MuiInputBase-root": {
                borderRadius: 3,
                bgcolor: "background.paper",
              },
            }}
          />
          <IconButton
            color="primary"
            onClick={handleSubmit}
            disabled={isPending || !text.trim()}
            sx={{
              alignSelf: "flex-end",
              mb: 0.25,
              bgcolor: "primary.main",
              color: "primary.contrastText",
              "&:hover": { bgcolor: "primary.dark" },
              "&.Mui-disabled": {
                bgcolor: "action.disabledBackground",
                color: "action.disabled",
              },
            }}
          >
            <FiSend />
          </IconButton>
        </Box>
      </DialogContent>
    </Dialog>
  )
}

export default AutoCheckinModal
