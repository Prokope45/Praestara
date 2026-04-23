import { Box, Container, Paper, Stack, Typography } from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import { ValueMapDiagram } from "@/components/ValueMap/ValueMapDiagram"

export const Route = createFileRoute("/_layout/value-map")({
  component: ValueMap,
})

function ValueMap() {
  return (
    <Container maxWidth={false}>
      <Stack spacing={3} sx={{ pt: 6 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Value Map
          </Typography>
          <Typography variant="body1" color="text.secondary">
            A living map of values, identity, and directional goals.
          </Typography>
        </Box>

        <Paper sx={{ height: 700, position: "relative", overflow: "hidden" }}>
          <ValueMapDiagram />
        </Paper>
      </Stack>
    </Container>
  )
}
