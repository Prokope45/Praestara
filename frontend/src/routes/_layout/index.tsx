import { Box, Container, Typography, Paper, Card, CardContent, Chip, Button, Stack } from "@mui/material"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useMemo } from "react"
import { FiTarget, FiCheckCircle, FiClock, FiTrendingUp, FiArrowRight } from "react-icons/fi"

import useAuth from "@/hooks/useAuth"
import { sampleObjectives } from "@/data/sampleObjectives"
import { getTempObjectives } from "@/utils/tempObjectiveStorage"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()
  const navigate = useNavigate()

  // Combine sample and temp objectives
  const allObjectives = useMemo(() => {
    const tempObjectives = getTempObjectives()
    return [...tempObjectives, ...sampleObjectives]
  }, [])

  // Calculate overall metrics
  const metrics = useMemo(() => {
    const totalObjectives = allObjectives.length
    const totalTasks = allObjectives.reduce((sum, obj) => sum + obj.tasks.length, 0)
    const completedTasks = allObjectives.reduce(
      (sum, obj) => sum + obj.tasks.filter((t) => !t.isActive).length,
      0
    )
    const activeTasks = totalTasks - completedTasks
    const percentComplete = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

    return {
      totalObjectives,
      totalTasks,
      completedTasks,
      activeTasks,
      percentComplete,
    }
  }, [allObjectives])

  // Get recent objectives (top 3)
  const recentObjectives = useMemo(() => {
    return allObjectives
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
      .slice(0, 3)
  }, [allObjectives])

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
              <FiTarget size={24} />
              <Typography variant="h6" sx={{ ml: 1 }}>
                Objectives
              </Typography>
            </Box>
            <Typography variant="h3" sx={{ fontWeight: "bold" }}>
              {metrics.totalObjectives}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
              Total active objectives
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
              <FiCheckCircle size={24} />
              <Typography variant="h6" sx={{ ml: 1 }}>
                Completed
              </Typography>
            </Box>
            <Typography variant="h3" sx={{ fontWeight: "bold" }}>
              {metrics.completedTasks}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
              Tasks finished
            </Typography>
          </Paper>

          <Paper
            sx={{
              p: 3,
              flex: 1,
              background: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
              color: "white",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <FiClock size={24} />
              <Typography variant="h6" sx={{ ml: 1 }}>
                Active
              </Typography>
            </Box>
            <Typography variant="h3" sx={{ fontWeight: "bold" }}>
              {metrics.activeTasks}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
              Tasks in progress
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
                Progress
              </Typography>
            </Box>
            <Typography variant="h3" sx={{ fontWeight: "bold" }}>
              {metrics.percentComplete}%
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
              Overall completion
            </Typography>
          </Paper>
        </Stack>

        {/* Recent Objectives */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
            <Typography variant="h5" sx={{ fontWeight: "bold" }}>
              Recent Objectives
            </Typography>
            <Button
              variant="outlined"
              endIcon={<FiArrowRight />}
              onClick={() => navigate({ to: "/tasks" })}
            >
              View All
            </Button>
          </Box>

          {recentObjectives.length === 0 ? (
            <Box sx={{ textAlign: "center", py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No objectives yet. Create your first objective to get started!
              </Typography>
              <Button
                variant="contained"
                sx={{ mt: 2 }}
                onClick={() => navigate({ to: "/tasks" })}
              >
                Create Objective
              </Button>
            </Box>
          ) : (
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              {recentObjectives.map((objective) => {
                const completedTasks = objective.tasks.filter((t) => !t.isActive).length
                const totalTasks = objective.tasks.length
                const percentComplete =
                  totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

                return (
                  <Card
                    key={objective.id}
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
                        to: "/tasks",
                        search: { objectiveId: objective.id },
                      })
                    }
                  >
                    <CardContent>
                      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: "bold" }}>
                          {objective.title}
                        </Typography>
                        {objective.id.startsWith("temp-") && (
                          <Chip label="Temp" size="small" color="warning" />
                        )}
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
                        {objective.description || "No description"}
                      </Typography>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          {completedTasks}/{totalTasks} tasks
                        </Typography>
                        <Chip
                          label={`${percentComplete}%`}
                          size="small"
                          color={percentComplete === 100 ? "success" : "default"}
                        />
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
              onClick={() => navigate({ to: "/tasks" })}
            >
              View Objectives
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
              onClick={() => navigate({ to: "/tasks" })}
            >
              Create Objective
            </Button>
          </Stack>
        </Paper>
      </Box>
    </Container>
  )
}
