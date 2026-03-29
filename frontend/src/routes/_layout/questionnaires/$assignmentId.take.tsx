import {
  Alert,
  Box,
  Container,
  LinearProgress,
  Paper,
  Stack,
  Typography,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useRef, useState } from "react"

import { type AnswerCreate, QuestionnairesService } from "../../../client"
import { AnimatedProgressBar } from "../../../components/Common/AnimatedProgressBar"
import { LikertScaleQuestion } from "../../../components/Questionnaires/LikertScaleQuestion"
import { Button } from "../../../components/ui/button"
import useCustomToast from "../../../hooks/useCustomToast"

export const Route = createFileRoute(
  "/_layout/questionnaires/$assignmentId/take",
)({
  component: TakeQuestionnaire,
})

const QUESTIONS_PER_PAGE = 5
const AUTOSAVE_DELAY = 30000 // 30 seconds

function TakeQuestionnaire() {
  const { assignmentId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()

  const [currentPage, setCurrentPage] = useState(0)
  const [answers, setAnswers] = useState<Record<string, any>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const autosaveTimerRef = useRef<NodeJS.Timeout | null>(null)

  const { data: assignment, isLoading } = useQuery({
    queryKey: ["questionnaire-assignment", assignmentId],
    queryFn: () => QuestionnairesService.readAssignment({ assignmentId }),
  })

  // Load saved progress when assignment loads
  useEffect(() => {
    if (assignment?.saved_progress) {
      // Handle both old format (just answers) and new format (with lastPage)
      if (
        assignment.saved_progress.answers &&
        typeof assignment.saved_progress.answers === "object"
      ) {
        setAnswers(assignment.saved_progress.answers)
        if (typeof assignment.saved_progress.lastPage === "number") {
          setCurrentPage(assignment.saved_progress.lastPage)
        }
      } else {
        // Backwards compatibility: old format was just the answers object
        setAnswers(assignment.saved_progress)
      }
    }
  }, [assignment])

  const saveProgressMutation = useMutation({
    mutationFn: (progress: Record<string, any>) =>
      QuestionnairesService.updateAssignmentProgress({
        assignmentId,
        requestBody: progress,
      }),
    onSuccess: () => {
      setHasUnsavedChanges(false)
      showSuccessToast("Progress saved")
    },
    onError: () => {
      showErrorToast("Failed to save progress")
    },
  })

  const submitMutation = useMutation({
    mutationFn: (data: { assignment_id: string; answers: AnswerCreate[] }) =>
      QuestionnairesService.createResponse({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Questionnaire submitted successfully")
      queryClient.invalidateQueries({ queryKey: ["questionnaire-assignments"] })
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      navigate({ to: "/questionnaires" })
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to submit questionnaire")
    },
  })

  // Autosave logic
  const saveProgress = useCallback(() => {
    if (hasUnsavedChanges && Object.keys(answers).length > 0) {
      saveProgressMutation.mutate({
        answers,
        lastPage: currentPage,
      })
    }
  }, [answers, currentPage, hasUnsavedChanges, saveProgressMutation])

  // Set up autosave timer
  useEffect(() => {
    if (hasUnsavedChanges) {
      if (autosaveTimerRef.current) {
        clearTimeout(autosaveTimerRef.current)
      }
      autosaveTimerRef.current = setTimeout(() => {
        saveProgress()
      }, AUTOSAVE_DELAY)
    }

    return () => {
      if (autosaveTimerRef.current) {
        clearTimeout(autosaveTimerRef.current)
      }
    }
  }, [hasUnsavedChanges, saveProgress])

  const questions = assignment?.questionnaire?.questions || []
  const sections = assignment?.questionnaire?.sections || []

  // Build pages based on sections
  const buildPages = () => {
    const sortedQuestions = [...questions].sort(
      (a, b) => (a.order ?? 0) - (b.order ?? 0),
    )
    const sortedSections = [...sections].sort(
      (a, b) => (a.order ?? 0) - (b.order ?? 0),
    )

    interface PageData {
      section?: any
      questions: any[]
      startIndex: number
      pageIndex: number
    }

    const pages: PageData[] = []
    let globalQuestionIdx = 0

    if (sortedSections.length > 0) {
      // Group by section
      sortedSections.forEach((section) => {
        // @ts-ignore - section_id is injected via openapi client generation but may not be typed immediately
        const sectionQuestions = sortedQuestions.filter(
          (q) => q.section_id === section.id,
        )
        if (sectionQuestions.length > 0) {
          for (
            let i = 0;
            i < sectionQuestions.length;
            i += QUESTIONS_PER_PAGE
          ) {
            const pageQuestions = sectionQuestions.slice(
              i,
              i + QUESTIONS_PER_PAGE,
            )
            pages.push({
              section,
              questions: pageQuestions,
              startIndex: globalQuestionIdx,
              pageIndex: pages.length,
            })
            globalQuestionIdx += pageQuestions.length
          }
        }
      })
      // Unsectioned questions
      // @ts-ignore
      const unsectionedQuestions = sortedQuestions.filter((q) => !q.section_id)
      if (unsectionedQuestions.length > 0) {
        for (
          let i = 0;
          i < unsectionedQuestions.length;
          i += QUESTIONS_PER_PAGE
        ) {
          const pageQuestions = unsectionedQuestions.slice(
            i,
            i + QUESTIONS_PER_PAGE,
          )
          pages.push({
            questions: pageQuestions,
            startIndex: globalQuestionIdx,
            pageIndex: pages.length,
          })
          globalQuestionIdx += pageQuestions.length
        }
      }
    } else {
      for (let i = 0; i < sortedQuestions.length; i += QUESTIONS_PER_PAGE) {
        const pageQuestions = sortedQuestions.slice(i, i + QUESTIONS_PER_PAGE)
        pages.push({
          questions: pageQuestions,
          startIndex: globalQuestionIdx,
          pageIndex: pages.length,
        })
        globalQuestionIdx += pageQuestions.length
      }
    }

    return pages
  }

  const pages = buildPages()
  const totalPages = pages.length
  // Ensure current page is within bounds
  const safeCurrentPage = Math.min(currentPage, Math.max(0, totalPages - 1))
  const currentPageData =
    pages[safeCurrentPage] || ({ questions: [], startIndex: 0 } as any)
  const currentPageQuestions = currentPageData.questions

  const handleAnswerChange = (questionId: string, value: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }))
    setHasUnsavedChanges(true)
    // Clear error for this question
    if (errors[questionId]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[questionId]
        return newErrors
      })
    }
  }

  const validateCurrentPage = () => {
    const newErrors: Record<string, string> = {}
    currentPageQuestions.forEach((question: any) => {
      if (question.is_required && !answers[question.id]) {
        newErrors[question.id] = "This question is required"
      }
    })
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const validateAllQuestions = () => {
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

  const handleNextPage = () => {
    if (validateCurrentPage()) {
      saveProgress() // Save when navigating
      setCurrentPage((prev) => prev + 1)
      window.scrollTo({ top: 0, behavior: "smooth" })
    } else {
      showErrorToast("Please answer all required questions on this page")
    }
  }

  const handlePreviousPage = () => {
    saveProgress() // Save when navigating
    setCurrentPage((prev) => prev - 1)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const handleSaveAndExit = async () => {
    if (Object.keys(answers).length > 0) {
      try {
        await saveProgressMutation.mutateAsync({
          answers,
          lastPage: currentPage,
        })
        navigate({ to: "/questionnaires" })
      } catch (error) {
        // Error toast already shown by mutation
      }
    } else {
      navigate({ to: "/questionnaires" })
    }
  }

  const handleSubmit = () => {
    if (!validateAllQuestions()) {
      showErrorToast("Please answer all required questions")
      // Find the first page with errors
      const questions = assignment?.questionnaire?.questions || []
      const sortedQuestions = [...questions].sort(
        (a, b) => (a.order ?? 0) - (b.order ?? 0),
      )
      for (let i = 0; i < sortedQuestions.length; i++) {
        const question = sortedQuestions[i]
        if (question.is_required && !answers[question.id]) {
          setCurrentPage(Math.floor(i / QUESTIONS_PER_PAGE))
          break
        }
      }
      return
    }

    const questions = assignment?.questionnaire?.questions || []
    const answersList: AnswerCreate[] = Object.entries(answers).map(
      ([questionId, value]) => {
        const question = questions.find((q) => q.id === questionId)
        const scaleType = question?.scale_type

        // Handle different scale types
        if (scaleType === "TEXT") {
          return {
            question_id: questionId,
            likert_value: null,
            text_response: value,
          }
        }
        if (scaleType === "DOMAIN_RATING") {
          return {
            question_id: questionId,
            likert_value: null,
            text_response: JSON.stringify(value),
          }
        }
        // LIKERT_5, LIKERT_7, YES_NO, CUSTOM_NUMERIC, FREQUENCY
        return {
          question_id: questionId,
          likert_value: value,
          text_response: null,
        }
      },
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

  const startIdx = currentPageData.startIndex

  const answeredCount = Object.keys(answers).length
  const progress =
    questions.length > 0 ? (answeredCount / questions.length) * 100 : 0

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

        <Alert severity="info" sx={{ mb: 3 }}>
          Your progress is saved automatically. You can pause and return to this
          questionnaire at any time.
        </Alert>

        {assignment.due_date && (
          <Alert severity="warning" sx={{ mb: 3 }}>
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
          <AnimatedProgressBar
            current={answeredCount}
            total={questions.length}
            percentage={progress}
            label="Progress"
          />
        </Box>

        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
        >
          <Typography variant="body2" color="text.secondary">
            Page {safeCurrentPage + 1} of {totalPages || 1}
          </Typography>
          {hasUnsavedChanges && (
            <Typography variant="caption" color="warning.main">
              Unsaved changes
            </Typography>
          )}
        </Stack>
      </Paper>

      {(currentPageData as any).section && (
        <Paper
          elevation={0}
          sx={{
            p: 3,
            mb: 4,
            bgcolor: "primary.50",
            borderLeft: "4px solid",
            borderColor: "primary.main",
          }}
        >
          <Typography variant="h6" fontWeight="bold">
            {(currentPageData as any).section.name}
          </Typography>
          {(currentPageData as any).section.description && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              {(currentPageData as any).section.description}
            </Typography>
          )}
        </Paper>
      )}

      <Box
        component="form"
        onSubmit={(e) => {
          e.preventDefault()
        }}
      >
        {currentPageQuestions.map((question, index) => (
          <LikertScaleQuestion
            key={question.id}
            questionText={question.question_text}
            questionNumber={startIdx + index + 1}
            scaleType={
              question.scale_type as
                | "LIKERT_5"
                | "LIKERT_7"
                | "YES_NO"
                | "CUSTOM_NUMERIC"
                | "TEXT"
                | "FREQUENCY"
                | "DOMAIN_RATING"
            }
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
          <Stack direction="row" spacing={2} justifyContent="space-between">
            <Button
              variant="outlined"
              onClick={handleSaveAndExit}
              disabled={
                submitMutation.isPending || saveProgressMutation.isPending
              }
              loading={saveProgressMutation.isPending}
            >
              Save & Exit
            </Button>

            <Stack direction="row" spacing={2}>
              {safeCurrentPage > 0 && (
                <Button
                  variant="outlined"
                  onClick={handlePreviousPage}
                  disabled={submitMutation.isPending}
                >
                  Previous
                </Button>
              )}

              {safeCurrentPage < totalPages - 1 ? (
                <Button
                  variant="contained"
                  onClick={handleNextPage}
                  disabled={submitMutation.isPending}
                >
                  Next
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  loading={submitMutation.isPending}
                  disabled={submitMutation.isPending}
                >
                  Submit Questionnaire
                </Button>
              )}
            </Stack>
          </Stack>
        </Paper>
      </Box>
    </Container>
  )
}
