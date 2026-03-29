import {
  Box,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { FiPlus, FiTrash2 } from "react-icons/fi"

import {
  type QuestionCreate,
  type QuestionSectionCreate,
  type QuestionnaireTemplatePublic,
  QuestionnairesService,
} from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { Button } from "../ui/button"

interface AddQuestionnaireProps {
  open: boolean
  onClose: () => void
  questionnaire?: QuestionnaireTemplatePublic
}

interface QuestionForm extends QuestionCreate {
  tempId: string
}

interface SectionForm extends QuestionSectionCreate {
  id: string
}

export function AddQuestionnaire({
  open,
  onClose,
  questionnaire,
}: AddQuestionnaireProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEditing = !!questionnaire

  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [isActive, setIsActive] = useState(true)
  const [sections, setSections] = useState<SectionForm[]>([])
  const [questions, setQuestions] = useState<QuestionForm[]>([])

  useEffect(() => {
    if (questionnaire) {
      setTitle(questionnaire.title)
      setDescription(questionnaire.description || "")
      setIsActive(questionnaire.is_active ?? true)
      setSections(
        (questionnaire.sections || []).map((s, index) => ({
          ...s,
          id: s.id || `existing-sec-${index}`,
        })) as SectionForm[],
      )
      setQuestions(
        questionnaire.questions?.map((q, index) => ({
          ...q,
          tempId: `existing-${index}`,
        })) || [],
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
        : QuestionnairesService.createQuestionnaireTemplate({
            requestBody: data,
          }),
    onSuccess: () => {
      showSuccessToast(
        isEditing
          ? "Questionnaire updated successfully"
          : "Questionnaire created successfully",
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
    setSections([])
    setQuestions([])
    onClose()
  }

  const addSection = () => {
    setSections([
      ...sections,
      {
        id: crypto.randomUUID
          ? crypto.randomUUID()
          : `sec-${Date.now()}-${Math.random()}`,
        name: "",
        description: "",
        order: sections.length,
      },
    ])
  }

  const removeSection = (id: string) => {
    setSections(sections.filter((s) => s.id !== id))
    // Also remove section_id from questions that used it
    setQuestions(
      questions.map((q) =>
        q.section_id === id ? { ...q, section_id: null } : q,
      ),
    )
  }

  const updateSection = (id: string, field: string, value: any) => {
    setSections(
      sections.map((s) => (s.id === id ? { ...s, [field]: value } : s)),
    )
  }

  const addQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_text: "",
        order: questions.length,
        is_required: true,
        scale_type: "LIKERT_5",
        section_id: null,
        custom_min_value: null,
        custom_max_value: null,
        custom_unit_label: null,
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
        q.tempId === tempId ? { ...q, [field]: value } : q,
      ),
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

    // Validate custom numeric questions
    const customQuestions = questions.filter(
      (q) => q.scale_type === "CUSTOM_NUMERIC",
    )
    for (const q of customQuestions) {
      if (
        q.custom_min_value === null ||
        q.custom_min_value === undefined ||
        q.custom_max_value === null ||
        q.custom_max_value === undefined
      ) {
        showErrorToast("Custom numeric questions must have min and max values")
        return
      }
      if (q.custom_min_value >= q.custom_max_value) {
        showErrorToast("Min value must be less than max value")
        return
      }
    }

    const sectionsData = sections.map((s, index) => ({
      id: s.id,
      name: s.name,
      description: s.description || null,
      order: index,
    }))

    const questionsData = questions.map((q, index) => ({
      question_text: q.question_text,
      order: index,
      is_required: q.is_required,
      scale_type: q.scale_type,
      section_id: q.section_id || null,
      custom_min_value:
        q.scale_type === "CUSTOM_NUMERIC" ? q.custom_min_value : null,
      custom_max_value:
        q.scale_type === "CUSTOM_NUMERIC" ? q.custom_max_value : null,
      custom_unit_label:
        q.scale_type === "CUSTOM_NUMERIC" ? q.custom_unit_label : null,
    }))

    createMutation.mutate({
      title,
      description: description || null,
      is_active: isActive,
      sections: sectionsData,
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
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ mb: 2 }}
            >
              <Typography variant="h6">Sections (Optional)</Typography>
              <Button
                variant="outlined"
                size="small"
                startIcon={<FiPlus />}
                onClick={addSection}
              >
                Add Section
              </Button>
            </Stack>

            <Stack spacing={2} sx={{ mb: 4 }}>
              {sections.map((section, index) => (
                <Box
                  key={section.id}
                  sx={{
                    p: 2,
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 1,
                    bgcolor: "info.lighter",
                  }}
                >
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    alignItems="flex-start"
                    spacing={2}
                  >
                    <Typography
                      variant="caption"
                      color="info.main"
                      sx={{ mt: 1 }}
                    >
                      Section {index + 1}
                    </Typography>
                    <Box sx={{ flex: 1 }}>
                      <TextField
                        label="Section Name"
                        value={section.name}
                        onChange={(e) =>
                          updateSection(section.id, "name", e.target.value)
                        }
                        fullWidth
                        size="small"
                        required
                        sx={{ mb: 2 }}
                      />
                      <TextField
                        label="Description (Optional)"
                        value={section.description || ""}
                        onChange={(e) =>
                          updateSection(
                            section.id,
                            "description",
                            e.target.value,
                          )
                        }
                        fullWidth
                        size="small"
                        multiline
                        rows={2}
                      />
                    </Box>
                    <IconButton
                      size="small"
                      onClick={() => removeSection(section.id)}
                      color="error"
                    >
                      <FiTrash2 />
                    </IconButton>
                  </Stack>
                </Box>
              ))}
            </Stack>
          </Box>

          <Box>
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ mb: 2 }}
            >
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
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    alignItems="flex-start"
                    spacing={2}
                  >
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ mt: 1 }}
                    >
                      #{index + 1}
                    </Typography>
                    <Box sx={{ flex: 1 }}>
                      <TextField
                        label="Question Text"
                        value={question.question_text}
                        onChange={(e) =>
                          updateQuestion(
                            question.tempId,
                            "question_text",
                            e.target.value,
                          )
                        }
                        fullWidth
                        size="small"
                        sx={{ mb: 2 }}
                      />
                      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                        {sections.length > 0 && (
                          <FormControl size="small" sx={{ minWidth: 150 }}>
                            <InputLabel>Section</InputLabel>
                            <Select
                              value={question.section_id || ""}
                              label="Section"
                              onChange={(e) =>
                                updateQuestion(
                                  question.tempId,
                                  "section_id",
                                  e.target.value || null,
                                )
                              }
                            >
                              <MenuItem value="">
                                <em>None</em>
                              </MenuItem>
                              {sections.map((s, idx) => (
                                <MenuItem key={s.id} value={s.id}>
                                  {s.name || `Section ${idx + 1}`}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        )}
                        <FormControl size="small" sx={{ minWidth: 150 }}>
                          <InputLabel>Scale Type</InputLabel>
                          <Select
                            value={question.scale_type}
                            label="Scale Type"
                            onChange={(e) =>
                              updateQuestion(
                                question.tempId,
                                "scale_type",
                                e.target.value,
                              )
                            }
                          >
                            <MenuItem value="LIKERT_5">Likert 5-Point</MenuItem>
                            <MenuItem value="LIKERT_7">Likert 7-Point</MenuItem>
                            <MenuItem value="YES_NO">Yes/No</MenuItem>
                            <MenuItem value="CUSTOM_NUMERIC">
                              Custom Numeric
                            </MenuItem>
                            <MenuItem value="TEXT">Text Response</MenuItem>
                            <MenuItem value="FREQUENCY">
                              Frequency (0-3)
                            </MenuItem>
                            <MenuItem value="DOMAIN_RATING">
                              Domain Rating
                            </MenuItem>
                          </Select>
                        </FormControl>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={question.is_required}
                              onChange={(e) =>
                                updateQuestion(
                                  question.tempId,
                                  "is_required",
                                  e.target.checked,
                                )
                              }
                              size="small"
                            />
                          }
                          label="Required"
                        />
                      </Stack>

                      {question.scale_type === "CUSTOM_NUMERIC" && (
                        <Box
                          sx={{
                            p: 2,
                            bgcolor: "background.paper",
                            border: "1px solid",
                            borderColor: "divider",
                            borderRadius: 1,
                          }}
                        >
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ mb: 1, display: "block" }}
                          >
                            Custom Scale Configuration
                          </Typography>
                          <Stack direction="row" spacing={2}>
                            <TextField
                              label="Min Value"
                              type="number"
                              value={question.custom_min_value ?? ""}
                              onChange={(e) =>
                                updateQuestion(
                                  question.tempId,
                                  "custom_min_value",
                                  e.target.value
                                    ? Number.parseInt(e.target.value)
                                    : null,
                                )
                              }
                              size="small"
                              required
                              sx={{ width: 120 }}
                            />
                            <TextField
                              label="Max Value"
                              type="number"
                              value={question.custom_max_value ?? ""}
                              onChange={(e) =>
                                updateQuestion(
                                  question.tempId,
                                  "custom_max_value",
                                  e.target.value
                                    ? Number.parseInt(e.target.value)
                                    : null,
                                )
                              }
                              size="small"
                              required
                              sx={{ width: 120 }}
                            />
                            <TextField
                              label="Unit Label (optional)"
                              value={question.custom_unit_label ?? ""}
                              onChange={(e) =>
                                updateQuestion(
                                  question.tempId,
                                  "custom_unit_label",
                                  e.target.value || null,
                                )
                              }
                              size="small"
                              placeholder="e.g., hours, times, walks"
                              sx={{ flex: 1 }}
                            />
                          </Stack>
                        </Box>
                      )}
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
