import { Box, Button, Container, Paper, Stack, TextField, Typography } from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import { useMutation } from "@tanstack/react-query"
import { useState } from "react"

import { AiService } from "@/client"

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

  const mutation = useMutation({
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
          content: "The assistant is unavailable right now. Please try again shortly.",
        },
      ])
    },
  })

  const sendMessage = () => {
    const trimmed = input.trim()
    if (!trimmed || mutation.isPending) {
      return
    }
    setMessages((prev) => [...prev, { role: "user", content: trimmed }])
    setInput("")
    mutation.mutate(trimmed)
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 1 }}>
          Praestara Chat
        </Typography>
        <Typography variant="body2" color="text.secondary">
          The assistant responds using the configured LLM endpoint.
        </Typography>
      </Paper>

      <Paper sx={{ p: 3, minHeight: 360 }}>
        <Stack spacing={2}>
          {messages.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              Start the conversation.
            </Typography>
          ) : (
            messages.map((message, index) => (
              <Box
                key={`${message.role}-${index}`}
                sx={{
                  alignSelf: message.role === "user" ? "flex-end" : "flex-start",
                  bgcolor: message.role === "user" ? "primary.main" : "grey.100",
                  color: message.role === "user" ? "primary.contrastText" : "text.primary",
                  px: 2,
                  py: 1.5,
                  borderRadius: 2,
                  maxWidth: "80%",
                }}
              >
                <Typography variant="body2">{message.content}</Typography>
              </Box>
            ))
          )}
        </Stack>
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
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault()
                sendMessage()
              }
            }}
          />
          <Button variant="contained" onClick={sendMessage} disabled={mutation.isPending}>
            {mutation.isPending ? "Sending..." : "Send"}
          </Button>
        </Stack>
      </Paper>
    </Container>
  )
}
