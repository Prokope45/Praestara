import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
} from "@mui/material"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { QuestionnairesService, type QuestionnaireTemplatePublic } from "../../client"
import { Button } from "../ui/button"
import useCustomToast from "../../hooks/useCustomToast"

interface DeleteQuestionnaireProps {
  open: boolean
  onClose: () => void
  questionnaire: QuestionnaireTemplatePublic
}

export function DeleteQuestionnaire({ open, onClose, questionnaire }: DeleteQuestionnaireProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: () =>
      QuestionnairesService.deleteQuestionnaireTemplate({ templateId: questionnaire.id }),
    onSuccess: () => {
      showSuccessToast("Questionnaire deleted successfully")
      queryClient.invalidateQueries({ queryKey: ["questionnaire-templates"] })
      onClose()
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to delete questionnaire")
    },
  })

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Delete Questionnaire</DialogTitle>
      <DialogContent>
        <Typography>
          Are you sure you want to delete "{questionnaire.title}"? This action cannot be undone.
        </Typography>
        {questionnaire.questions && questionnaire.questions.length > 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This will also delete {questionnaire.questions.length} question(s).
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={deleteMutation.isPending}>
          Cancel
        </Button>
        <Button
          onClick={() => deleteMutation.mutate()}
          variant="contained"
          color="error"
          loading={deleteMutation.isPending}
          disabled={deleteMutation.isPending}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  )
}
