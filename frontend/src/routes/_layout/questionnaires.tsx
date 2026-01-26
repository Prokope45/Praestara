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
} from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { FiClock, FiCheckCircle, FiAlertCircle } from "react-icons/fi"

import { QuestionnairesService, type QuestionnaireAssignmentPublic } from "../../client"
import { Button } from "../../components/ui/button"

export const Route = createFileRoute("/_layout/questionnaires")({
  component: Questionnaires,
})

function Questionnaires() {
  const { data: assignments, isLoading } = useQuery({
    queryKey: ["questionnaire-assignments"],
    queryFn: () => QuestionnairesService.readMyAssignments({ skip: 0, limit: 100 }),
  })

  const pendingAssignments = assignments?.data?.filter(
    (a: QuestionnaireAssignmentPublic) => a.status === "PENDING"
  )
  const completedAssignments = assignments?.data?.filter(
    (a: QuestionnaireAssignmentPublic) => a.status === "COMPLETED"
  )

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
                  <Link to={`/questionnaires/${assignment.id}/take`}>
                    <Button variant="contained" size="small">
                      Take Questionnaire
                    </Button>
                  </Link>
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
