import {
  Box,
  Card,
  CardContent,
  Chip,
  IconButton,
  LinearProgress,
  Stack,
  Typography,
} from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { FiEdit, FiPlus, FiTrash2, FiUserPlus, FiUsers } from "react-icons/fi"

import {
  type QuestionnaireTemplatePublic,
  QuestionnairesService,
} from "../../client"
import { AddQuestionnaire } from "../../components/Questionnaires/AddQuestionnaire"
import { AssignQuestionnaire } from "../../components/Questionnaires/AssignQuestionnaire"
import { DeleteQuestionnaire } from "../../components/Questionnaires/DeleteQuestionnaire"
import { ViewAssignments } from "../../components/Questionnaires/ViewAssignments"
import { Button } from "../../components/ui/button"

export default function AdminQuestionnaires() {
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [editingQuestionnaire, setEditingQuestionnaire] =
    useState<QuestionnaireTemplatePublic | null>(null)
  const [deletingQuestionnaire, setDeletingQuestionnaire] =
    useState<QuestionnaireTemplatePublic | null>(null)
  const [assigningQuestionnaire, setAssigningQuestionnaire] =
    useState<QuestionnaireTemplatePublic | null>(null)
  const [viewingAssignments, setViewingAssignments] =
    useState<QuestionnaireTemplatePublic | null>(null)

  const { data: questionnaires, isLoading } = useQuery({
    queryKey: ["questionnaire-templates"],
    queryFn: () =>
      QuestionnairesService.readQuestionnaireTemplates({ skip: 0, limit: 100 }),
  })

  if (isLoading) {
    return <LinearProgress />
  }

  const isNotOnboardingQuestionnaire = (q: QuestionnaireTemplatePublic) => q.title != "Onboarding Questionnaire"

  return (
    <Box>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 4 }}
      >
        <Box>
          <Typography
            variant="h5"
            component="h2"
            gutterBottom
            fontWeight="bold"
          >
            Questionnaire Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Create and manage questionnaires for users
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<FiPlus />}
          onClick={() => setShowAddDialog(true)}
          sx={{ alignSelf: { xs: "stretch", sm: "auto" } }}
        >
          Create Questionnaire
        </Button>
      </Stack>

      {questionnaires?.data && questionnaires.data.length > 0 ? (
        <Stack spacing={2}>
          {questionnaires.data.map(
            (questionnaire: QuestionnaireTemplatePublic) => (
              <Card key={questionnaire.id} variant="outlined">
                <CardContent>
                  <Stack
                    direction={{ xs: "column", md: "row" }}
                    justifyContent="space-between"
                    alignItems={{ xs: "stretch", md: "flex-start" }}
                    spacing={2}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Stack
                        direction="row"
                        spacing={2}
                        alignItems="center"
                        sx={{ mb: 1 }}
                        flexWrap="wrap"
                        useFlexGap
                      >
                        <Typography variant="h6" component="h3">
                          {questionnaire.title}
                        </Typography>
                        <Chip
                          label={
                            questionnaire.is_active ? "Active" : "Inactive"
                          }
                          color={
                            questionnaire.is_active ? "success" : "default"
                          }
                          size="small"
                        />
                      </Stack>
                      {questionnaire.description && (
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mb: 2 }}
                        >
                          {questionnaire.description}
                        </Typography>
                      )}
                      <Stack direction={{ xs: "column", sm: "row" }} spacing={{ xs: 1, sm: 3 }}>
                        <Typography variant="caption" color="text.secondary">
                          <strong>Questions:</strong>{" "}
                          {questionnaire.questions?.length || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          <strong>Created:</strong>{" "}
                          {new Date(
                            questionnaire.created_at,
                          ).toLocaleDateString()}
                        </Typography>
                      </Stack>
                    </Box>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: { xs: 2, md: 0 } }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<FiUsers />}
                        onClick={() => setViewingAssignments(questionnaire)}
                      >
                        View Assigned
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<FiUserPlus />}
                        onClick={() => setAssigningQuestionnaire(questionnaire)}
                      >
                        Assign
                      </Button>
                      <IconButton
                        size="small"
                        onClick={() => setEditingQuestionnaire(questionnaire)}
                        color="primary"
                      >
                        <FiEdit />
                      </IconButton>
                      {isNotOnboardingQuestionnaire(questionnaire)
                        ?? (
                          <IconButton
                            size="small"
                            onClick={() => setDeletingQuestionnaire(questionnaire)}
                            color="error"
                          >
                            <FiTrash2 />
                          </IconButton>
                        )
                      }
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            ),
          )}
        </Stack>
      ) : (
        <Card variant="outlined">
          <CardContent>
            <Typography
              color="text.secondary"
              textAlign="center"
              sx={{ py: 4 }}
            >
              No questionnaires created yet. Click "Create Questionnaire" to get
              started.
            </Typography>
          </CardContent>
        </Card>
      )}

      {showAddDialog && (
        <AddQuestionnaire
          open={showAddDialog}
          onClose={() => setShowAddDialog(false)}
        />
      )}

      {editingQuestionnaire && (
        <AddQuestionnaire
          open={!!editingQuestionnaire}
          onClose={() => setEditingQuestionnaire(null)}
          questionnaire={editingQuestionnaire}
        />
      )}

      {deletingQuestionnaire && (
        <DeleteQuestionnaire
          open={!!deletingQuestionnaire}
          onClose={() => setDeletingQuestionnaire(null)}
          questionnaire={deletingQuestionnaire}
        />
      )}

      {assigningQuestionnaire && (
        <AssignQuestionnaire
          open={!!assigningQuestionnaire}
          onClose={() => setAssigningQuestionnaire(null)}
          questionnaire={assigningQuestionnaire}
        />
      )}

      {viewingAssignments && (
        <ViewAssignments
          open={!!viewingAssignments}
          onClose={() => setViewingAssignments(null)}
          questionnaire={viewingAssignments}
        />
      )}
    </Box>
  )
}
