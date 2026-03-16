import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Chip,
  Stack,
  LinearProgress,
  Paper,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiClock, FiCheckCircle, FiAlertCircle } from "react-icons/fi"

import { QuestionnairesService, type QuestionnaireAssignmentPublic } from "../../client"
import { appFlowApi } from "../../api/appFlow"
import { Button } from "../../components/ui/button"
import { PendingQuestionnaireWidget } from "../../components/Questionnaires/PendingQuestionnaireWidget"
import useCustomToast from "../../hooks/useCustomToast"

export const Route = createFileRoute("/_layout/questionnaires/")({
  component: Questionnaires,
})

function Questionnaires() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { data: assignments, isLoading } = useQuery({
    queryKey: ["questionnaire-assignments"],
    queryFn: () => QuestionnairesService.readMyAssignments({ skip: 0, limit: 100 }),
  })
  const { data: flow } = useQuery({
    queryKey: ["app-flow"],
    queryFn: appFlowApi.getFlow,
  })

  const pendingAssignments = assignments?.data?.filter(
    (a: QuestionnaireAssignmentPublic) => a.status === "PENDING"
  )
  const completedAssignments = assignments?.data?.filter(
    (a: QuestionnaireAssignmentPublic) => a.status === "COMPLETED"
  )
  const onboardingAssignment = pendingAssignments?.find(
    (assignment: QuestionnaireAssignmentPublic) =>
      assignment.questionnaire.title === "Praestara Onboarding"
  )

  const refreshState = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["questionnaire-assignments"] }),
      queryClient.invalidateQueries({ queryKey: ["questionnaire-assignments", "me"] }),
      queryClient.invalidateQueries({ queryKey: ["app-flow"] }),
      queryClient.invalidateQueries({ queryKey: ["goal-scaffold", "goals"] }),
      queryClient.invalidateQueries({ queryKey: ["self-concept", "snapshot"] }),
      queryClient.invalidateQueries({ queryKey: ["self-concept", "history"] }),
      queryClient.invalidateQueries({ queryKey: ["week-setup"] }),
      queryClient.invalidateQueries({ queryKey: ["alignment", "today"] }),
    ])
  }

  const resetMutation = useMutation({
    mutationFn: async () => {
      const { devPresetsApi } = await import("../../api/devPresets")
      return devPresetsApi.reset()
    },
    onSuccess: async () => {
      await refreshState()
      showSuccessToast("Local preset state cleared")
    },
    onError: () => {
      showErrorToast("Unable to reset local state")
    },
  })

  const getStatusColor = (status: string | undefined) => {
    switch (status) {
      case "PENDING":
        return "warning"
      case "COMPLETED":
        return "success"
      case "OVERDUE":
        return "error"
      default:
        return "default"
    }
  }

  const getStatusIcon = (status: string | undefined) => {
    switch (status) {
      case "PENDING":
        return <FiClock />
      case "COMPLETED":
        return <FiCheckCircle />
      case "OVERDUE":
        return <FiAlertCircle />
      default:
        return null
    }
  }

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return "No due date"
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <LinearProgress />
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
        My Questionnaires
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Complete your assigned questionnaires to help track your progress
      </Typography>

      <Paper
        sx={{
          p: 3,
          mb: 4,
          border: "2px solid",
          borderColor: "warning.main",
          bgcolor: "warning.50",
        }}
      >
        <Stack spacing={2}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Local Presets
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Use this instead of redoing onboarding. These buttons load a canned baseline directly into the app.
            </Typography>
          </Box>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <Button
              variant="contained"
              onClick={() => (window.location.href = "/week-setup?devPreset=week_setup")}
              disabled={resetMutation.isPending}
            >
              Load To Week Setup
            </Button>
            <Button
              variant="contained"
              onClick={() => (window.location.href = "/alignment/today?devPreset=today_ready")}
              disabled={resetMutation.isPending}
            >
              Load To Today
            </Button>
            <Button
              variant="outlined"
              onClick={() => resetMutation.mutate()}
              disabled={resetMutation.isPending}
            >
              Reset State
            </Button>
          </Stack>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Stack spacing={2}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Current App State
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Baseline: {flow?.has_baseline ? "ready" : "not set"} | Week setup:{" "}
              {flow?.week_setup_confirmed ? "confirmed" : "not confirmed"} | Next action:{" "}
              {flow?.pending_action ?? "none"}
            </Typography>
          </Box>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <Button variant="outlined" onClick={() => (window.location.href = "/week-setup")}>
              Open Week Setup
            </Button>
            <Button variant="outlined" onClick={() => (window.location.href = "/alignment/today")}>
              Open Today
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {onboardingAssignment ? (
        <Box sx={{ mb: 4 }}>
          <PendingQuestionnaireWidget assignment={onboardingAssignment} />
        </Box>
      ) : null}

      {/* Pending Questionnaires */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 3 }}>
          Pending ({pendingAssignments?.length || 0})
        </Typography>
        {pendingAssignments && pendingAssignments.length > 0 ? (
          <Stack spacing={2}>
            {pendingAssignments.map((assignment: QuestionnaireAssignmentPublic) => (
              <Card key={assignment.id} variant="outlined">
                <CardContent>
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    alignItems="flex-start"
                    sx={{ mb: 2 }}
                  >
                    <Box>
                      <Typography variant="h6" component="h3">
                        {assignment.questionnaire.title}
                      </Typography>
                      {assignment.questionnaire.description && (
                        <Typography variant="body2" color="text.secondary">
                          {assignment.questionnaire.description}
                        </Typography>
                      )}
                    </Box>
                    <Chip
                      label={assignment.status}
                      color={getStatusColor(assignment.status) as any}
                      icon={getStatusIcon(assignment.status) as any}
                      size="small"
                    />
                  </Stack>
                  <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      <strong>Assigned:</strong>{" "}
                      {formatDate(assignment.assigned_at)}
                    </Typography>
                    {assignment.due_date && (
                      <Typography variant="caption" color="text.secondary">
                        <strong>Due:</strong> {formatDate(assignment.due_date)}
                      </Typography>
                    )}
                    <Typography variant="caption" color="text.secondary">
                      <strong>Questions:</strong>{" "}
                      {assignment.questionnaire.questions?.length || 0}
                    </Typography>
                  </Stack>
                </CardContent>
                <CardActions>
                  <Button 
                    variant="contained" 
                    size="small"
                    onClick={() => {
                      navigate({
                        to: "/questionnaires/$assignmentId/take",
                        params: { assignmentId: assignment.id }
                      })
                    }}
                  >
                    {assignment.questionnaire.title === "Praestara Onboarding"
                      ? assignment.saved_progress && Object.keys(assignment.saved_progress).length > 0
                        ? "Resume Onboarding"
                        : "Start Onboarding"
                      : assignment.saved_progress && Object.keys(assignment.saved_progress).length > 0
                        ? "Resume Questionnaire"
                        : "Take Questionnaire"}
                  </Button>
                </CardActions>
              </Card>
            ))}
          </Stack>
        ) : (
          <Card variant="outlined">
            <CardContent>
              <Typography color="text.secondary" textAlign="center">
                No pending questionnaires
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>

      {/* Completed Questionnaires */}
      <Box>
        <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 3 }}>
          Completed ({completedAssignments?.length || 0})
        </Typography>
        {completedAssignments && completedAssignments.length > 0 ? (
          <Stack spacing={2}>
            {completedAssignments.map((assignment: QuestionnaireAssignmentPublic) => (
              <Card key={assignment.id} variant="outlined">
                <CardContent>
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    alignItems="flex-start"
                  >
                    <Box>
                      <Typography variant="h6" component="h3">
                        {assignment.questionnaire.title}
                      </Typography>
                      {assignment.questionnaire.description && (
                        <Typography variant="body2" color="text.secondary">
                          {assignment.questionnaire.description}
                        </Typography>
                      )}
                    </Box>
                    <Chip
                      label={assignment.status}
                      color={getStatusColor(assignment.status) as any}
                      icon={getStatusIcon(assignment.status) as any}
                      size="small"
                    />
                  </Stack>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: "block" }}>
                    <strong>Completed:</strong> {formatDate(assignment.assigned_at)}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        ) : (
          <Card variant="outlined">
            <CardContent>
              <Typography color="text.secondary" textAlign="center">
                No completed questionnaires yet
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>
    </Container>
  )
}
