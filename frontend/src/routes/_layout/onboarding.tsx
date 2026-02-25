import { Button, Container, Paper, Stack, Typography } from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import useAuth from "@/hooks/useAuth"
import OnboardingQuestionnaire from "@/components/Onboarding/OnboardingQuestionnaire"

export const Route = createFileRoute("/_layout/onboarding")({
  component: Onboarding,
})

function Onboarding() {
  const { user: currentUser } = useAuth()
  const [showForm, setShowForm] = useState(false)

  if (currentUser?.onboarding_completed_at) {
    return (
      <Container maxWidth="md" sx={{ py: 6 }}>
        {showForm ? (
          <OnboardingQuestionnaire />
        ) : (
          <Paper sx={{ p: 3 }}>
            <Stack spacing={2}>
              <Typography variant="h5">Onboarding complete</Typography>
              <Typography variant="body1" color="text.secondary">
                You already completed the baseline questionnaire. You can revisit it to create
                a new baseline if needed.
              </Typography>
              <Button variant="outlined" onClick={() => setShowForm(true)}>
                Start a new baseline
              </Button>
            </Stack>
          </Paper>
        )}
      </Container>
    )
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <OnboardingQuestionnaire />
    </Container>
  )
}
