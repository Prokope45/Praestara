import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
  Stack,
  CircularProgress,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { FiTrash2, FiUser } from "react-icons/fi"

import { QuestionnairesService, UsersService, type QuestionnaireTemplatePublic } from "../../client"
import { Button } from "../ui/button"
import useCustomToast from "../../hooks/useCustomToast"

interface ViewAssignmentsProps {
  open: boolean
  onClose: () => void
  questionnaire: QuestionnaireTemplatePublic
}

export function ViewAssignments({ open, onClose, questionnaire }: ViewAssignmentsProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Fetch assignments for this questionnaire
  const { data: assignmentsData, isLoading } = useQuery({
    queryKey: ["questionnaire-assignments", questionnaire.id],
    queryFn: () =>
      QuestionnairesService.readAllAssignments({
        questionnaireId: questionnaire.id,
        skip: 0,
        limit: 1000,
      }),
    enabled: open,
  })

  // Fetch all users to display names
  const { data: usersData } = useQuery({
    queryKey: ["users"],
    queryFn: () => UsersService.readUsers({ skip: 0, limit: 1000 }),
    enabled: open,
  })

  const deleteAssignmentMutation = useMutation({
    mutationFn: (assignmentId: string) =>
      QuestionnairesService.deleteAssignment({ assignmentId }),
    onSuccess: () => {
      showSuccessToast("Assignment removed successfully")
      queryClient.invalidateQueries({ queryKey: ["questionnaire-assignments"] })
      queryClient.invalidateQueries({ queryKey: ["all-assignments"] })
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to remove assignment")
    },
  })

  const handleRemoveAssignment = (assignmentId: string) => {
    if (confirm("Are you sure you want to remove this assignment?")) {
      deleteAssignmentMutation.mutate(assignmentId)
    }
  }

  const getUserName = (userId: string) => {
    const user = usersData?.data?.find((u) => u.id === userId)
    return user?.full_name || user?.email || "Unknown User"
  }

  const getUserEmail = (userId: string) => {
    const user = usersData?.data?.find((u) => u.id === userId)
    return user?.email || ""
  }

  const getStatusColor = (status: string) => {
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

  const pendingAssignments = assignmentsData?.data?.filter((a: any) => a.status === "PENDING") || []
  const completedAssignments = assignmentsData?.data?.filter((a: any) => a.status === "COMPLETED") || []

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" spacing={1}>
          <FiUser />
          <Typography variant="h6">Assigned Users</Typography>
        </Stack>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3}>
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Questionnaire
            </Typography>
            <Box
              sx={{
                p: 2,
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 1,
                bgcolor: "background.paper",
              }}
            >
              <Typography variant="body1" fontWeight="medium">
                {questionnaire.title}
              </Typography>
              {questionnaire.description && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {questionnaire.description}
                </Typography>
              )}
            </Box>
          </Box>

          {isLoading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {/* Pending Assignments */}
              <Box>
                <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                  Pending Assignments ({pendingAssignments.length})
                </Typography>
                {pendingAssignments.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    No pending assignments
                  </Typography>
                ) : (
                  <List sx={{ bgcolor: "background.paper", borderRadius: 1, border: "1px solid", borderColor: "divider" }}>
                    {pendingAssignments.map((assignment: any, index: number) => (
                      <ListItem
                        key={assignment.id}
                        divider={index < pendingAssignments.length - 1}
                        secondaryAction={
                          <IconButton
                            edge="end"
                            aria-label="delete"
                            onClick={() => handleRemoveAssignment(assignment.id)}
                            disabled={deleteAssignmentMutation.isPending}
                          >
                            <FiTrash2 />
                          </IconButton>
                        }
                      >
                        <ListItemText
                          primary={
                            <Stack direction="row" alignItems="center" spacing={1}>
                              <Typography variant="body1">{getUserName(assignment.user_id)}</Typography>
                              <Chip
                                label={assignment.status}
                                size="small"
                                color={getStatusColor(assignment.status) as any}
                              />
                            </Stack>
                          }
                          secondary={
                            <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">
                                {getUserEmail(assignment.user_id)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Assigned: {new Date(assignment.assigned_at).toLocaleDateString()}
                                {assignment.due_date && ` • Due: ${new Date(assignment.due_date).toLocaleDateString()}`}
                              </Typography>
                            </Stack>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>

              {/* Completed Assignments */}
              {completedAssignments.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                    Completed Assignments ({completedAssignments.length})
                  </Typography>
                  <List sx={{ bgcolor: "background.paper", borderRadius: 1, border: "1px solid", borderColor: "divider" }}>
                    {completedAssignments.map((assignment: any, index: number) => (
                      <ListItem
                        key={assignment.id}
                        divider={index < completedAssignments.length - 1}
                      >
                        <ListItemText
                          primary={
                            <Stack direction="row" alignItems="center" spacing={1}>
                              <Typography variant="body1">{getUserName(assignment.user_id)}</Typography>
                              <Chip
                                label={assignment.status}
                                size="small"
                                color={getStatusColor(assignment.status) as any}
                              />
                            </Stack>
                          }
                          secondary={
                            <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">
                                {getUserEmail(assignment.user_id)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Assigned: {new Date(assignment.assigned_at).toLocaleDateString()}
                              </Typography>
                            </Stack>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
