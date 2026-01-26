import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Checkbox,
  Select,
  MenuItem,
  Box,
  Stack,
  IconButton,
  Typography,
  FormControl,
  InputLabel,
} from "@mui/material"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState, useEffect } from "react"
import { FiPlus, FiTrash2 } from "react-icons/fi"

import { QuestionnairesService, type QuestionnaireTemplatePublic, type QuestionCreate } from "../../client"
import { Button } from "../ui/button"
import useCustomToast from "../../hooks/useCustomToast"

interface AddQuestionnaireProps {
  open: boolean
  onClose: () => void
  questionnaire?: QuestionnaireTemplatePublic
}

interface QuestionForm extends QuestionCreate {
  tempId: string
}

export function AddQuestionnaire({ open, onClose, questionnaire }: AddQuestionnaireProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEditing = !!questionnaire

  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [isActive, setIsActive] = useState(true)
  const [questions, setQuestions] = useState<QuestionForm[]>([])

  useEffect(() => {
    if (questionnaire) {
      setTitle(questionnaire.title)
      setDescription(questionnaire.description || "")
      setIsActive(questionnaire.is_active ?? true)
      setQuestions(
        questionnaire.questions?.map((q, index) => ({
          ...q,
          tempId: `existing-${index}`,
        })) || []
      )
    }
  }, [questionnaire])

  const createMutation = useMutation({
    mutationFn: (data: any) =>
      isEditing
        ? QuestionnairesService.updateQuestionnaireTemplate({
            templateId: questionnaire.id,
            requestBody: data,
          })
        : QuestionnairesService.createQuestionnaireTemplate({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast(
        isEditing ? "Questionnaire updated successfully" : "Questionnaire created successfully"
      )
      queryClient.invalidateQueries({ queryKey: ["questionnaire-templates"] })
      handleClose()
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to save questionnaire")
    },
  })

  const handleClose = () => {
    setTitle("")
    setDescription("")
    setIsActive(true)
    setQuestions([])
    onClose()
  }

  const addQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_text: "",
        order: questions.length,
        is_required: true,
        scale_type: "LIKERT_5",
        tempId: `new-${Date.now()}`,
      },
    ])
  }

  const removeQuestion = (tempId: string) => {
    setQuestions(questions.filter((q) => q.tempId !== tempId))
  }

  const updateQuestion = (tempId: string, field: string, value: any) => {
    setQuestions(
      questions.map((q) =>
        q.tempId === tempId ? { ...q, [field]: value } : q
      )
    )
  }

  const handleSubmit = () => {
    if (!title.trim()) {
      showErrorToast("Please enter a title")
      return
    }

    if (questions.length === 0) {
      showErrorToast("Please add at least one question")
      return
    }

    const invalidQuestions = questions.filter((q) => !q.question_text.trim())
    if (invalidQuestions.length > 0) {
      showErrorToast("All questions must have text")
      return
    }

    const questionsData = questions.map((q, index) => ({
      question_text: q.question_text,
      order: index,
      is_required: q.is_required,
      scale_type: q.scale_type,
    }))

    createMutation.mutate({
      title,
      description: description || null,
      is_active: isActive,
      questions: questionsData,
    })
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isEditing ? "Edit Questionnaire" : "Create New Questionnaire"}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 2 }}>
          <TextField
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
            multiline
            rows={2}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
            }
            label="Active"
          />

          <Box>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6">Questions</Typography>
              <Button
                variant="outlined"
                size="small"
                startIcon={<FiPlus />}
                onClick={addQuestion}
              >
                Add Question
              </Button>
            </Stack>

            <Stack spacing={2}>
              {questions.map((question, index) => (
                <Box
                  key={question.tempId}
                  sx={{
                    p: 2,
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 1,
                  }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      #{index + 1}
                    </Typography>
                    <Box sx={{ flex: 1 }}>
                      <TextField
                        label="Question Text"
                        value={question.question_text}
                        onChange={(e) =>
                          updateQuestion(question.tempId, "question_text", e.target.value)
                        }
                        fullWidth
                        size="small"
                        sx={{ mb: 2 }}
                      />
                      <Stack direction="row" spacing={2}>
                        <FormControl size="small" sx={{ minWidth: 150 }}>
                          <InputLabel>Scale Type</InputLabel>
                          <Select
                            value={question.scale_type}
                            label="Scale Type"
                            onChange={(e) =>
                              updateQuestion(question.tempId, "scale_type", e.target.value)
                            }
                          >
                            <MenuItem value="LIKERT_5">Likert 5-Point</MenuItem>
                            <MenuItem value="LIKERT_7">Likert 7-Point</MenuItem>
                            <MenuItem value="YES_NO">Yes/No</MenuItem>
                          </Select>
                        </FormControl>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={question.is_required}
                              onChange={(e) =>
                                updateQuestion(question.tempId, "is_required", e.target.checked)
                              }
                              size="small"
                            />
                          }
                          label="Required"
                        />
                      </Stack>
                    </Box>
                    <IconButton
                      size="small"
                      onClick={() => removeQuestion(question.tempId)}
                      color="error"
                    >
                      <FiTrash2 />
                    </IconButton>
                  </Stack>
                </Box>
              ))}
            </Stack>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={createMutation.isPending}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          loading={createMutation.isPending}
          disabled={createMutation.isPending}
        >
          {isEditing ? "Update" : "Create"}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
