import { Box, Button, Container, Paper, Stack, TextField, Typography } from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { CheckinsService, QuestionnairesService } from "@/client"

export const Route = createFileRoute("/_layout/checkins")({
  component: Checkins,
})

const splitIntoSentences = (text: string) => {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
}

function Checkins() {
  const [morningText, setMorningText] = useState("")
  const [eveningText, setEveningText] = useState("")
  const [morningReply, setMorningReply] = useState<string | null>(null)
  const [eveningReply, setEveningReply] = useState<string | null>(null)

  const morningMutation = useMutation({
    mutationFn: (text: string) =>
      CheckinsService.createCheckin({ requestBody: { type: "morning", text } }),
    onSuccess: (response) => {
      setMorningReply(response.reply)
    },
  })

  const eveningMutation = useMutation({
    mutationFn: (text: string) =>
      CheckinsService.createCheckin({ requestBody: { type: "evening", text } }),
    onSuccess: (response) => {
      setEveningReply(response.reply)
    },
  })

  const { data: morningHistory } = useQuery({
    queryKey: ["checkins", "morning"],
    queryFn: () =>
      QuestionnairesService.readLegacyQuestionnaireResponses({
        kind: "morning_checkin",
        limit: 10,
      }),
  })

  const { data: eveningHistory } = useQuery({
    queryKey: ["checkins", "evening"],
    queryFn: () =>
      QuestionnairesService.readLegacyQuestionnaireResponses({
        kind: "evening_checkin",
        limit: 10,
      }),
  })

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Stack spacing={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ mb: 1 }}>
            Check‑in history snapshot
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Last 10 morning and evening check‑ins (demo data seeded).
          </Typography>
          <Stack direction={{ xs: "column", md: "row" }} spacing={3} sx={{ mt: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>
                Morning
              </Typography>
              {morningHistory?.data?.map((entry) => (
                <Box key={entry.id} sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    {new Date(entry.created_at).toLocaleDateString()}
                  </Typography>
                  <Stack spacing={0.5}>
                    {splitIntoSentences((entry.payload as any).text ?? "").map((sentence, idx) => (
                      <Typography key={idx} variant="body2">
                        {sentence}
                      </Typography>
                    ))}
                  </Stack>
                </Box>
              ))}
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>
                Evening
              </Typography>
              {eveningHistory?.data?.map((entry) => (
                <Box key={entry.id} sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    {new Date(entry.created_at).toLocaleDateString()}
                  </Typography>
                  <Stack spacing={0.5}>
                    {splitIntoSentences((entry.payload as any).text ?? "").map((sentence, idx) => (
                      <Typography key={idx} variant="body2">
                        {sentence}
                      </Typography>
                    ))}
                  </Stack>
                </Box>
              ))}
            </Box>
          </Stack>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ mb: 1 }}>
            Good morning. Who are you going to be today?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Describe today.
          </Typography>
          <Stack spacing={2}>
            <TextField
              value={morningText}
              onChange={(event) => setMorningText(event.target.value)}
              placeholder="Today I plan to..."
              fullWidth
              multiline
              minRows={4}
            />
            <Button
              variant="contained"
              onClick={() => morningMutation.mutate(morningText)}
              disabled={morningMutation.isPending || !morningText.trim()}
            >
              {morningMutation.isPending ? "Sending..." : "Submit morning check‑in"}
            </Button>
            {morningReply && (
              <Box sx={{ mt: 2, p: 2, bgcolor: "grey.100", borderRadius: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Praestara reflection
                </Typography>
                <Typography variant="body2">{morningReply}</Typography>
              </Box>
            )}
          </Stack>
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ mb: 1 }}>
            Good evening. Who were you today?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Describe today.
          </Typography>
          <Stack spacing={2}>
            <TextField
              value={eveningText}
              onChange={(event) => setEveningText(event.target.value)}
              placeholder="Today I..."
              fullWidth
              multiline
              minRows={4}
            />
            <Button
              variant="contained"
              onClick={() => eveningMutation.mutate(eveningText)}
              disabled={eveningMutation.isPending || !eveningText.trim()}
            >
              {eveningMutation.isPending ? "Sending..." : "Submit evening check‑in"}
            </Button>
            {eveningReply && (
              <Box sx={{ mt: 2, p: 2, bgcolor: "grey.100", borderRadius: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Praestara reflection
                </Typography>
                <Typography variant="body2">{eveningReply}</Typography>
              </Box>
            )}
          </Stack>
        </Paper>
      </Stack>
    </Container>
  )
}
