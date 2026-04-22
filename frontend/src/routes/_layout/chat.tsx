import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline"
import {
  Box,
  Button,
  CircularProgress,
  Container,
  IconButton,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useRef, useState } from "react"

import { AiService, CheckinsService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import CheckinTimeline from "@/components/Checkins/CheckinTimeline"

export const Route = createFileRoute("/_layout/chat")({
  component: Chat,
})

interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

function Chat() {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [selectedCheckins, setSelectedCheckins] = useState<Set<string>>(new Set())
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const showToast = useCustomToast()
  const queryClient = useQueryClient()

  // For constructing context
  const { data: checkinsResponse } = useQuery({
    queryKey: ["checkins", "timeline", 7],
    queryFn: () => CheckinsService.readCheckinTimeline({ days: 7 }),
  })

  const toggleSelection = (id: string) => {
    setSelectedCheckins((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  // Fetch chat history on mount
  const { data: historyData, isLoading: isLoadingHistory } = useQuery({
    queryKey: ["chatHistory"],
    queryFn: () => AiService.getChatHistory(),
  })

  // Update messages when history is loaded
  useEffect(() => {
    if (historyData && Array.isArray(historyData.history)) {
      const loadedMessages: ChatMessage[] = historyData.history.map(
        (msg: any) => ({
          role: msg.role as "user" | "assistant",
          content: msg.content,
        }),
      )
      setMessages(loadedMessages)
    }
  }, [historyData])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" })
  }, [messages])

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) =>
      AiService.chatWithAi({
        requestBody: { message },
      }),
    onSuccess: (response) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.message },
      ])
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "The assistant is unavailable right now. Please try again shortly.",
        },
      ])
    },
  })

  // Clear history mutation
  const clearHistoryMutation = useMutation({
    mutationFn: () => AiService.clearChatHistory(),
    onSuccess: () => {
      setMessages([])
      showToast.showSuccessToast("Chat history cleared")
      queryClient.invalidateQueries({ queryKey: ["chatHistory"] })
    },
    onError: () => {
      showToast.showErrorToast("Failed to clear chat history")
    },
  })

  const sendMessage = () => {
    const trimmed = input.trim()
    if (!trimmed || sendMessageMutation.isPending) {
      return
    }

    let finalMessage = trimmed
    if (selectedCheckins.size > 0) {
      const checkinsContext = Array.from(selectedCheckins)
        .map((id) => {
          const checkin = checkinsResponse?.data.find((c) => c.id === id)
          if (!checkin) return ""
          return `[${checkin.type.toUpperCase()} CHECK-IN - ${new Date(checkin.created_at).toLocaleDateString()}]\n${checkin.text}`
        })
        .filter(Boolean)
        .join("\n\n")

      finalMessage = `Context from selected check-ins:\n${checkinsContext}\n\nUser message:\n${trimmed}`
    }

    setMessages((prev) => [...prev, { role: "user", content: finalMessage }])
    setInput("")
    setSelectedCheckins(new Set())
    sendMessageMutation.mutate(finalMessage)
  }

  const handleClearHistory = () => {
    if (messages.length === 0) return
    clearHistoryMutation.mutate()
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 2}}
        >
          <Box>
            <Typography variant="h5" sx={{ mb: 1 }}>
              Praestara Chat
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Chat with the AI assistant powered by Koios RAG. Your conversation
              history is saved automatically.
            </Typography>
          </Box>
          <Tooltip title="Clear chat history">
            <span>
              <IconButton
                onClick={handleClearHistory}
                disabled={
                  messages.length === 0 || clearHistoryMutation.isPending
                }
                color="error"
              >
                {clearHistoryMutation.isPending ? (
                  <CircularProgress size={24} />
                ) : (
                  <DeleteOutlineIcon />
                )}
              </IconButton>
            </span>
          </Tooltip>
        </Stack>

        <hr />

        <Stack>
          <Typography variant="body1" sx={{ mb: 1 }}>
            Check-in Timeline
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select past check-ins to include them as context for your conversation.
          </Typography>

          <Box sx={{ position: "relative", py: 2, overflowX: "auto" }}>
            <CheckinTimeline selectedCheckins={selectedCheckins} toggleSelection={toggleSelection} />
          </Box>
        </Stack>
      </Paper>

      <Paper
        sx={{
          p: 3,
          minHeight: 360,
          maxHeight: 500,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {isLoadingHistory ? (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              flexGrow: 1,
            }}
          >
            <CircularProgress />
          </Box>
        ) : messages.length === 0 ? (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: "center", mt: 4 }}
          >
            Start the conversation. Your messages will be saved and restored
            when you return.
          </Typography>
        ) : (
          <Stack spacing={2} sx={{ flexGrow: 1 }}>
            {messages.map((message, index) => (
              <Box
                key={`${message.role}-${index}`}
                sx={{
                  alignSelf:
                    message.role === "user" ? "flex-end" : "flex-start",
                  bgcolor:
                    message.role === "user" ? "primary.main" : "grey.100",
                  color:
                    message.role === "user"
                      ? "primary.contrastText"
                      : "text.primary",
                  px: 2,
                  py: 1.5,
                  borderRadius: 2,
                  maxWidth: "80%",
                  wordBreak: "break-word",
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                  {message.content}
                </Typography>
              </Box>
            ))}
            {sendMessageMutation.isPending && (
              <Box
                sx={{
                  alignSelf: "flex-start",
                  bgcolor: "grey.100",
                  px: 2,
                  py: 1.5,
                  borderRadius: 2,
                }}
              >
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontStyle: "italic" }}
                >
                  Assistant is thinking...
                </Typography>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Stack>
        )}
      </Paper>

      <Paper sx={{ p: 2, mt: 3 }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            fullWidth
            placeholder="Write a message..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            autoFocus
            multiline
            minRows={2}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault()
                sendMessage()
              }
            }}
          />
          <Button
            variant="contained"
            onClick={sendMessage}
            disabled={sendMessageMutation.isPending || !input.trim()}
            sx={{ minWidth: 100 }}
          >
            {sendMessageMutation.isPending ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              "Send"
            )}
          </Button>
        </Stack>
      </Paper>
    </Container>
  )
}
