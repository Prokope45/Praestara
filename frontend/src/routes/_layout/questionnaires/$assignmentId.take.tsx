import {
  Container,
  Typography,
  Box,
  LinearProgress,
  Alert,
  Paper,
  Stack,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import { QuestionnairesService, type AnswerCreate } from "../../../client"
import { Button } from "../../../components/ui/button"
import { LikertScaleQuestion } from "../../../components/Questionnaires/LikertScaleQuestion"
import useCustomToast from "../../../hooks/useCustomToast"

export const Route = createFileRoute("/_layout/questionnaires/$assignmentId/take")({
  component: TakeQuestionnaire,
})

function TakeQuestionnaire() {
  const { assignmentId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()

  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  const { data: assignment, isLoading } = useQuery({
    queryKey: ["questionnaire-assignment", assignmentId],
    queryFn: () => QuestionnairesService.readAssignment({ assignmentId }),
  })

  const submitMutation = useMutation({
    mutationFn: (data: { assignment_id: string; answers: AnswerCreate[] }) =>
      QuestionnairesService.createResponse({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Questionnaire submitted successfully")
      queryClient.invalidateQueries({ queryKey: ["questionnaire-assignments"] })
      navigate({ to: "/questionnaires" })
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to submit questionnaire")
    },
  })

  const handleAnswerChange = (questionId: string, value: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }))
    // Clear error for this question
    if (errors[questionId]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[questionId]
        return newErrors
      })
    }
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    const questions = assignment?.questionnaire?.questions || []

    questions.forEach((question) => {
      if (question.is_required && !answers[question.id]) {
        newErrors[question.id] = "This question is required"
      }
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = () => {
    if (!validateForm()) {
      showErrorToast("Please answer all required questions")
      return
    }

    const answersList: AnswerCreate[] = Object.entries(answers).map(
      ([questionId, value]) => ({
        question_id: questionId,
        likert_value: value,
        text_response: null,
      })
    )

    submitMutation.mutate({
      assignment_id: assignmentId,
      answers: answersList,
    })
  }

  if (isLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <LinearProgress />
      </Container>
    )
  }

  if (!assignment) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">Assignment not found</Alert>
      </Container>
    )
  }

  if (assignment.status === "COMPLETED") {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="info">
          You have already completed this questionnaire.
        </Alert>
        <Button
          onClick={() => navigate({ to: "/questionnaires" })}
          sx={{ mt: 2 }}
        >
          Back to Questionnaires
        </Button>
      </Container>
    )
  }

  const questions = assignment.questionnaire?.questions || []
  const answeredCount = Object.keys(answers).length
  const progress = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={0} sx={{ p: 4, mb: 4, bgcolor: "background.paper" }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
          {assignment.questionnaire.title}
        </Typography>
        {assignment.questionnaire.description && (
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            {assignment.questionnaire.description}
          </Typography>
        )}

        {assignment.due_date && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <strong>Due:</strong>{" "}
            {new Date(assignment.due_date).toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </Alert>
        )}

        <Box sx={{ mb: 4 }}>
          <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Progress: {answeredCount} of {questions.length} questions answered
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {Math.round(progress)}%
            </Typography>
          </Stack>
          <LinearProgress variant="determinate" value={progress} />
        </Box>
      </Paper>

      <Box component="form" onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        {questions
          .sort((a, b) => a.order - b.order)
          .map((question, index) => (
            <LikertScaleQuestion
              key={question.id}
              questionText={question.question_text}
              questionNumber={index + 1}
              scaleType={question.scale_type as "LIKERT_5" | "LIKERT_7" | "YES_NO" | "CUSTOM_NUMERIC"}
              isRequired={question.is_required || false}
              value={answers[question.id] || null}
              onChange={(value) => handleAnswerChange(question.id, value)}
              error={errors[question.id]}
              customMinValue={question.custom_min_value}
              customMaxValue={question.custom_max_value}
              customUnitLabel={question.custom_unit_label}
            />
          ))}

        <Paper elevation={0} sx={{ p: 3, mt: 4, bgcolor: "background.paper" }}>
          <Stack direction="row" spacing={2} justifyContent="flex-end">
            <Button
              variant="outlined"
              onClick={() => navigate({ to: "/questionnaires" })}
              disabled={submitMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              loading={submitMutation.isPending}
              disabled={submitMutation.isPending}
            >
              Submit Questionnaire
            </Button>
          </Stack>
        </Paper>
      </Box>
    </Container>
  )
}
