import {
  Box,
  Card,
  CardContent,
  Chip,
  Stack,
  LinearProgress,
  IconButton,
  Typography,
} from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { FiEdit, FiTrash2, FiPlus } from "react-icons/fi"
import { useState } from "react"

import { QuestionnairesService, type QuestionnaireTemplatePublic } from "../../client"
import { Button } from "../../components/ui/button"
import { AddQuestionnaire } from "../../components/Questionnaires/AddQuestionnaire"
import { DeleteQuestionnaire } from "../../components/Questionnaires/DeleteQuestionnaire"

export default function AdminQuestionnaires() {
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [editingQuestionnaire, setEditingQuestionnaire] = useState<QuestionnaireTemplatePublic | null>(null)
  const [deletingQuestionnaire, setDeletingQuestionnaire] = useState<QuestionnaireTemplatePublic | null>(null)

  const { data: questionnaires, isLoading } = useQuery({
    queryKey: ["questionnaire-templates"],
    queryFn: () => QuestionnairesService.readQuestionnaireTemplates({ skip: 0, limit: 100 }),
  })

  if (isLoading) {
    return <LinearProgress />
  }

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
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
        >
          Create Questionnaire
        </Button>
      </Stack>

      {questionnaires && questionnaires.data && questionnaires.data.length > 0 ? (
        <Stack spacing={2}>
          {questionnaires.data.map((questionnaire: QuestionnaireTemplatePublic) => (
            <Card key={questionnaire.id} variant="outlined">
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Box sx={{ flex: 1 }}>
                    <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
                      <Typography variant="h6" component="h3">
                        {questionnaire.title}
                      </Typography>
                      <Chip
                        label={questionnaire.is_active ? "Active" : "Inactive"}
                        color={questionnaire.is_active ? "success" : "default"}
                        size="small"
                      />
                    </Stack>
                    {questionnaire.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {questionnaire.description}
                      </Typography>
                    )}
                    <Stack direction="row" spacing={3}>
                      <Typography variant="caption" color="text.secondary">
                        <strong>Questions:</strong> {questionnaire.questions?.length || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        <strong>Created:</strong>{" "}
                        {new Date(questionnaire.created_at).toLocaleDateString()}
                      </Typography>
                    </Stack>
                  </Box>
                  <Stack direction="row" spacing={1}>
                    <IconButton
                      size="small"
                      onClick={() => setEditingQuestionnaire(questionnaire)}
                      color="primary"
                    >
                      <FiEdit />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => setDeletingQuestionnaire(questionnaire)}
                      color="error"
                    >
                      <FiTrash2 />
                    </IconButton>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      ) : (
        <Card variant="outlined">
          <CardContent>
            <Typography color="text.secondary" textAlign="center" sx={{ py: 4 }}>
              No questionnaires created yet. Click "Create Questionnaire" to get started.
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
    </Box>
  )
}
