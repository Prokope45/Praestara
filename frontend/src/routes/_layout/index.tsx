import { Box, Container, Typography } from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <>
      <Container maxWidth={false}>
        <Box sx={{ pt: 6, m: 2 }}>
          <Typography variant="h4" component="h1">
            Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
          </Typography>
          <Typography variant="body1" sx={{ mt: 1 }}>
            Welcome back, nice to see you again!
          </Typography>
        </Box>
      </Container>
    </>
  )
}
