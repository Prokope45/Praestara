import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  type QuestionnaireTemplatePublic,
  QuestionnairesService,
} from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { DeleteConfirmation } from "../Common/DeleteConfirmation"

interface DeleteQuestionnaireProps {
  open: boolean
  onClose: () => void
  questionnaire: QuestionnaireTemplatePublic
}

export function DeleteQuestionnaire({
  open,
  onClose,
  questionnaire,
}: DeleteQuestionnaireProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: () =>
      QuestionnairesService.deleteQuestionnaireTemplate({
        templateId: questionnaire.id,
      }),
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
    <DeleteConfirmation
      open={open}
      onClose={onClose}
      onConfirm={() => deleteMutation.mutate()}
      title="Delete Questionnaire"
      description={`Are you sure you want to delete "${questionnaire.title}"? This action cannot be undone.`}
      subDescription={
        questionnaire.questions && questionnaire.questions.length > 0
          ? `This will also delete ${questionnaire.questions.length} question(s).`
          : undefined
      }
      isPending={deleteMutation.isPending}
    />
  )
}
