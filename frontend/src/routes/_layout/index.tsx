import { Box, Container, Typography, Paper, Card, CardContent, Chip, Button, Stack } from "@mui/material"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { FiCompass, FiTrendingUp, FiArrowRight, FiTarget } from "react-icons/fi"

import useAuth from "@/hooks/useAuth"
import { OrientationsService } from "@/client"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()
  const navigate = useNavigate()

  // Fetch orientations from API
  const { data: orientationsData } = useQuery({
    queryKey: ["orientations"],
    queryFn: () => OrientationsService.readOrientations({ limit: 100 }),
  })

  const allOrientations = useMemo(() => {
    return orientationsData?.data || []
  }, [orientationsData])

  // Calculate overall metrics
  const metrics = useMemo(() => {
    const totalOrientations = allOrientations.length
    const totalTraits = allOrientations.reduce((sum, ori) => sum + (ori.traits?.length || 0), 0)
    const averageTraitValue =
      totalTraits > 0
        ? Math.round(
            allOrientations.reduce(
              (sum, ori) => sum + (ori.traits?.reduce((s, t) => s + t.value, 0) || 0),
              0
            ) / totalTraits
          )
        : 0

    return {
      totalOrientations,
      totalTraits,
      averageTraitValue,
    }
  }, [allOrientations])

  // Get recent orientations (top 3) - just take the first 3 since API returns them sorted
  const recentOrientations = useMemo(() => {
    return allOrientations.slice(0, 3)
  }, [allOrientations])

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6, pb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ mb: 1 }}>
          Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Welcome back! Here's your progress overview.
        </Typography>

        {/* Metrics Cards */}
        <Stack direction={{ xs: "column", sm: "row" }} spacing={3} sx={{ mb: 4 }}>
          <Paper
            sx={{
              p: 3,
              flex: 1,
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              color: "white",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <FiCompass size={24} />
              <Typography variant="h6" sx={{ ml: 1 }}>
                Orientations
              </Typography>
            </Box>
            <Typography variant="h3" sx={{ fontWeight: "bold" }}>
              {metrics.totalOrientations}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
              Active orientations
            </Typography>
          </Paper>

          <Paper
            sx={{
              p: 3,
              flex: 1,
              background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
              color: "white",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <FiTarget size={24} />
              <Typography variant="h6" sx={{ ml: 1 }}>
                Traits
              </Typography>
            </Box>
            <Typography variant="h3" sx={{ fontWeight: "bold" }}>
              {metrics.totalTraits}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
              Total traits tracked
            </Typography>
          </Paper>

          <Paper
            sx={{
              p: 3,
              flex: 1,
              background: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
              color: "white",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <FiTrendingUp size={24} />
              <Typography variant="h6" sx={{ ml: 1 }}>
                Average Level
              </Typography>
            </Box>
            <Typography variant="h3" sx={{ fontWeight: "bold" }}>
              {metrics.averageTraitValue}%
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
              Across all traits
            </Typography>
          </Paper>
        </Stack>

        {/* Recent Orientations */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
            <Typography variant="h5" sx={{ fontWeight: "bold" }}>
              Recent Orientations
            </Typography>
            <Button
              variant="outlined"
              endIcon={<FiArrowRight />}
              onClick={() => navigate({ to: "/orientations" })}
            >
              View All
            </Button>
          </Box>

          {recentOrientations.length === 0 ? (
            <Box sx={{ textAlign: "center", py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No orientations yet. Create your first orientation to get started!
              </Typography>
              <Button
                variant="contained"
                sx={{ mt: 2 }}
                onClick={() => navigate({ to: "/orientations" })}
              >
                Create Orientation
              </Button>
            </Box>
          ) : (
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              {recentOrientations.map((orientation) => {
                const totalTraits = orientation.traits?.length || 0
                const averageValue =
                  totalTraits > 0
                    ? Math.round(
                        (orientation.traits?.reduce((sum, trait) => sum + trait.value, 0) || 0) /
                          totalTraits
                      )
                    : 0

                return (
                  <Card
                    key={orientation.id}
                    sx={{
                      flex: 1,
                      cursor: "pointer",
                      transition: "transform 0.2s, box-shadow 0.2s",
                      "&:hover": {
                        transform: "translateY(-4px)",
                        boxShadow: 4,
                      },
                    }}
                    onClick={() =>
                      navigate({
                        to: "/orientations",
                        search: { orientationId: orientation.id },
                      })
                    }
                  >
                    <CardContent>
                      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: "bold" }}>
                          {orientation.title}
                        </Typography>
                      </Box>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mb: 2,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical",
                        }}
                      >
                        {orientation.description || "No description"}
                      </Typography>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          {totalTraits} traits
                        </Typography>
                        {totalTraits > 0 && (
                          <Chip
                            label={`${averageValue}% avg`}
                            size="small"
                            color={averageValue >= 70 ? "success" : "default"}
                          />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                )
              })}
            </Stack>
          )}
        </Paper>

        {/* Quick Actions */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: "bold", mb: 3 }}>
            Quick Actions
          </Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <Button
              variant="outlined"
              fullWidth
              sx={{ py: 2 }}
              onClick={() => navigate({ to: "/orientations" })}
            >
              View Orientations
            </Button>
            <Button
              variant="outlined"
              fullWidth
              sx={{ py: 2 }}
              onClick={() => navigate({ to: "/notes" })}
            >
              View Notes
            </Button>
            <Button
              variant="outlined"
              fullWidth
              sx={{ py: 2 }}
              onClick={() => navigate({ to: "/settings" })}
            >
              Settings
            </Button>
            <Button
              variant="contained"
              fullWidth
              sx={{ py: 2 }}
              onClick={() => navigate({ to: "/orientations" })}
            >
              Create Orientation
            </Button>
          </Stack>
        </Paper>
      </Box>
    </Container>
  )
}
