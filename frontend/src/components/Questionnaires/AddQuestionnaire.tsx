import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
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
  Menu,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import React, { useEffect, useState } from "react"
import { FiChevronDown, FiMove, FiPlus, FiTrash2 } from "react-icons/fi"

import {
  type QuestionCreate,
  type QuestionSectionCreate,
  type QuestionnaireTemplatePublic,
  QuestionnairesService,
} from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { DeleteConfirmation } from "../Common/DeleteConfirmation"
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

  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({})
  const [draggedSectionId, setDraggedSectionId] = useState<string | null>(null)

  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([])
  const [selectedSections, setSelectedSections] = useState<string[]>([])

  const [addAnchorEl, setAddAnchorEl] = useState<null | HTMLElement>(null)
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean
    type: "section" | "question" | "bulk"
    id?: string
  }>({ open: false, type: "section" })

  const [moveAnchorEl, setMoveAnchorEl] = useState<null | HTMLElement>(null)
  const [questionToMove, setQuestionToMove] = useState<string | null>(null)

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
    setExpandedSections({})
    setSelectedQuestions([])
    setSelectedSections([])
    onClose()
  }

  const addSection = () => {
    const newId = crypto.randomUUID
      ? crypto.randomUUID()
      : `sec-${Date.now()}-${Math.random()}`
    setSections([
      ...sections,
      {
        id: newId,
        name: "New Section",
        description: "",
        order: sections.length,
      },
    ])
    setExpandedSections((prev) => ({ ...prev, [newId]: true }))
  }

  const handleRemoveSection = (id: string) => {
    // Nested modal with focused background triggers warning; blur active element.
    (document.activeElement as HTMLElement)?.blur()
    setDeleteDialog({ open: true, type: "section", id })
  }

  const removeSection = (id: string) => {
    setSections(sections.filter((s) => s.id !== id))
    setQuestions(
      questions.map((q) =>
        q.section_id === id ? { ...q, section_id: null } : q,
      ),
    )
    setSelectedSections((prev) => prev.filter((secId) => secId !== id))
  }

  const updateSection = (id: string, field: string, value: any) => {
    setSections(
      sections.map((s) => (s.id === id ? { ...s, [field]: value } : s)),
    )
  }

  const addQuestion = (sectionId: string | null = null) => {
    setQuestions([
      ...questions,
      {
        question_text: "",
        order: questions.length,
        is_required: true,
        scale_type: "LIKERT_5",
        section_id: sectionId,
        custom_min_value: null,
        custom_max_value: null,
        custom_unit_label: null,
        tempId: `new-${Date.now()}-${Math.random()}`,
      },
    ])
  }

  const handleRemoveQuestion = (tempId: string) => {
    // Nested modal with focused background triggers warning; blur active element.
    (document.activeElement as HTMLElement)?.blur()
    setDeleteDialog({ open: true, type: "question", id: tempId })
  }

  const removeQuestion = (tempId: string) => {
    setQuestions(questions.filter((q) => q.tempId !== tempId))
    setSelectedQuestions((prev) => prev.filter((id) => id !== tempId))
  }

  const updateQuestion = (tempId: string, field: string, value: any) => {
    setQuestions(
      questions.map((q) =>
        q.tempId === tempId ? { ...q, [field]: value } : q,
      ),
    )
  }

  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDraggedSectionId(id)
    e.dataTransfer.effectAllowed = "move"
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = "move"
  }

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault()
    if (!draggedSectionId || draggedSectionId === targetId) return

    const newSections = [...sections]
    const draggedIndex = newSections.findIndex((s) => s.id === draggedSectionId)
    const targetIndex = newSections.findIndex((s) => s.id === targetId)

    const [draggedSection] = newSections.splice(draggedIndex, 1)
    newSections.splice(targetIndex, 0, draggedSection)

    const updatedSections = newSections.map((s, idx) => ({ ...s, order: idx }))
    setSections(updatedSections)
    setDraggedSectionId(null)
  }

  const openMoveMenu = (
    event: React.MouseEvent<HTMLElement>,
    questionTempId: string | null = null,
  ) => {
    setMoveAnchorEl(event.currentTarget)
    setQuestionToMove(questionTempId)
  }

  const closeMoveMenu = () => {
    setMoveAnchorEl(null)
    setQuestionToMove(null)
  }

  const moveQuestion = (sectionId: string | null) => {
    if (questionToMove) {
      updateQuestion(questionToMove, "section_id", sectionId)
    } else if (selectedQuestions.length > 0) {
      setQuestions(
        questions.map((q) =>
          selectedQuestions.includes(q.tempId)
            ? { ...q, section_id: sectionId }
            : q,
        ),
      )
    }
    closeMoveMenu()
  }

  const toggleQuestionSelection = (tempId: string) => {
    setSelectedQuestions((prev) =>
      prev.includes(tempId)
        ? prev.filter((id) => id !== tempId)
        : [...prev, tempId],
    )
  }

  const toggleSectionSelection = (id: string) => {
    setSelectedSections((prev) =>
      prev.includes(id) ? prev.filter((secId) => secId !== id) : [...prev, id],
    )
  }

  const handleBulkDelete = () => {
    // Nested modal with focused background triggers warning; blur active element.
    (document.activeElement as HTMLElement)?.blur()
    setDeleteDialog({ open: true, type: "bulk" })
  }

  const confirmDelete = () => {
    if (deleteDialog.type === "section" && deleteDialog.id) {
      removeSection(deleteDialog.id)
    } else if (deleteDialog.type === "question" && deleteDialog.id) {
      removeQuestion(deleteDialog.id)
    } else if (deleteDialog.type === "bulk") {
      if (selectedSections.length > 0) {
        setSections(sections.filter((s) => !selectedSections.includes(s.id)))
        setQuestions(
          questions.map((q) =>
            q.section_id && selectedSections.includes(q.section_id)
              ? { ...q, section_id: null }
              : q,
          ),
        )
      }
      if (selectedQuestions.length > 0) {
        setQuestions((prev) =>
          prev.filter((q) => !selectedQuestions.includes(q.tempId)),
        )
      }
      setSelectedSections([])
      setSelectedQuestions([])
    }
    setDeleteDialog({ open: false, type: "section" })
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

  const renderQuestion = (question: QuestionForm, index: number) => (
    <Box
      key={question.tempId}
      sx={{
        p: 2,
        mb: 2,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        bgcolor: selectedQuestions.includes(question.tempId)
          ? "action.selected"
          : "background.paper",
      }}
    >
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="flex-start"
        spacing={2}
      >
        <Checkbox
          checked={selectedQuestions.includes(question.tempId)}
          onChange={() => toggleQuestionSelection(question.tempId)}
          size="small"
        />
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
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
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
                <MenuItem value="CUSTOM_NUMERIC">Custom Numeric</MenuItem>
                <MenuItem value="TEXT">Text Response</MenuItem>
                <MenuItem value="FREQUENCY">Frequency (0-3)</MenuItem>
                <MenuItem value="DOMAIN_RATING">Domain Rating</MenuItem>
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
                bgcolor: "background.default",
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
                      e.target.value ? Number.parseInt(e.target.value) : null,
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
                      e.target.value ? Number.parseInt(e.target.value) : null,
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
        <Stack direction="row" spacing={1}>
          <IconButton
            size="small"
            onClick={(e) => openMoveMenu(e, question.tempId)}
            color="primary"
            title="Move"
          >
            <FiMove />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleRemoveQuestion(question.tempId)}
            color="error"
            title="Delete"
          >
            <FiTrash2 />
          </IconButton>
        </Stack>
      </Stack>
    </Box>
  )

  const unsectionedQuestions = questions.filter((q) => q.section_id === null)
  const isBulkActionsVisible =
    selectedQuestions.length > 0 || selectedSections.length > 0

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

          <Stack
            direction="row"
            spacing={2}
            sx={{ mb: 2, alignItems: "center" }}
          >
            <Button
              variant="outlined"
              startIcon={<FiPlus />}
              onClick={(e) => setAddAnchorEl(e.currentTarget)}
            >
              Add
            </Button>
            <Menu
              anchorEl={addAnchorEl}
              open={Boolean(addAnchorEl)}
              onClose={() => setAddAnchorEl(null)}
            >
              <MenuItem
                onClick={() => {
                  addSection()
                  setAddAnchorEl(null)
                }}
              >
                Section
              </MenuItem>
              <MenuItem
                onClick={() => {
                  addQuestion(null)
                  setAddAnchorEl(null)
                }}
              >
                Question
              </MenuItem>
            </Menu>
            {isBulkActionsVisible && (
              <>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<FiTrash2 />}
                  onClick={handleBulkDelete}
                >
                  Delete Selected
                </Button>
                {selectedQuestions.length > 0 && (
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<FiMove />}
                    onClick={(e) => openMoveMenu(e as any)}
                  >
                    Move Selected Questions
                  </Button>
                )}
              </>
            )}
          </Stack>

          <Box>
            {sections.map((section, index) => {
              const sectionQuestions = questions.filter(
                (q) => q.section_id === section.id,
              )
              const isSelected = selectedSections.includes(section.id)

              return (
                <Box
                  key={section.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, section.id)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, section.id)}
                  sx={{
                    mb: 2,
                    opacity: draggedSectionId === section.id ? 0.5 : 1,
                    border: isSelected ? "2px solid" : "none",
                    borderColor: "primary.main",
                    borderRadius: 1,
                  }}
                >
                  <Accordion
                    expanded={expandedSections[section.id] || false}
                    onChange={(_, expanded) =>
                      setExpandedSections((prev) => ({
                        ...prev,
                        [section.id]: expanded,
                      }))
                    }
                    sx={{
                      border: "1px solid",
                      borderColor: "divider",
                      boxShadow: "none",
                    }}
                  >
                    <AccordionSummary
                      expandIcon={<FiChevronDown />}
                      sx={{ bgcolor: "info.lighter" }}
                    >
                      <Stack
                        direction="row"
                        spacing={2}
                        alignItems="center"
                        sx={{ width: "100%" }}
                      >
                        <Checkbox
                          checked={isSelected}
                          onChange={(e) => {
                            e.stopPropagation()
                            toggleSectionSelection(section.id)
                          }}
                          onClick={(e) => e.stopPropagation()}
                          size="small"
                        />
                        <div
                          style={{ cursor: "grab", display: "flex" }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <FiMove />
                        </div>
                        <Typography
                          variant="subtitle1"
                          sx={{ flex: 1, fontWeight: "bold" }}
                        >
                          {section.name || `Section ${index + 1}`}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRemoveSection(section.id)
                          }}
                          color="error"
                          sx={{ paddingRight: "8px" }}
                        >
                          <FiTrash2 />
                        </IconButton>
                      </Stack>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Stack spacing={2}>
                        <TextField
                          label="Section Name"
                          value={section.name}
                          onChange={(e) =>
                            updateSection(section.id, "name", e.target.value)
                          }
                          fullWidth
                          size="small"
                          required
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
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" sx={{ mb: 1 }}>
                            Questions in this Section
                          </Typography>
                          {sectionQuestions.map((q, idx) =>
                            renderQuestion(q, idx),
                          )}
                          <Button
                            variant="text"
                            startIcon={<FiPlus />}
                            onClick={() => addQuestion(section.id)}
                            size="small"
                          >
                            Add Question to Section
                          </Button>
                        </Box>
                      </Stack>
                    </AccordionDetails>
                  </Accordion>
                </Box>
              )
            })}

            {/* General Questions (Unsectioned) */}
            {(unsectionedQuestions.length > 0 || sections.length === 0) && (
              <Box sx={{ mb: 2, mt: sections.length > 0 ? 4 : 0 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  {sections.length > 0 ? "General Questions" : "Questions"}
                </Typography>
                {unsectionedQuestions.map((q, idx) => renderQuestion(q, idx))}
                {sections.length > 0 && (
                  <Button
                    variant="text"
                    startIcon={<FiPlus />}
                    onClick={() => addQuestion(null)}
                    size="small"
                  >
                    Add General Question
                  </Button>
                )}
              </Box>
            )}
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

      {/* Move Question Menu */}
      <Menu
        anchorEl={moveAnchorEl}
        open={Boolean(moveAnchorEl)}
        onClose={closeMoveMenu}
      >
        <MenuItem onClick={() => moveQuestion(null)}>
          <em>General Questions</em>
        </MenuItem>
        {sections.map((s) => (
          <MenuItem key={s.id} onClick={() => moveQuestion(s.id)}>
            {s.name || "Unnamed Section"}
          </MenuItem>
        ))}
      </Menu>

      <DeleteConfirmation
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, type: "section" })}
        onConfirm={confirmDelete}
        title={
          deleteDialog.type === "bulk"
            ? "Delete Selected"
            : `Delete ${deleteDialog.type === "section" ? "Section" : "Question"}`
        }
        description={
          deleteDialog.type === "bulk"
            ? `Are you sure you want to delete ${
                selectedSections.length > 0 && selectedQuestions.length > 0
                  ? `${selectedSections.length} section(s) and ${selectedQuestions.length} question(s)`
                  : selectedSections.length > 0
                    ? `${selectedSections.length} section(s)`
                    : `${selectedQuestions.length} question(s)`
              }? This action cannot be undone.`
            : `Are you sure you want to delete this ${deleteDialog.type}? This action cannot be undone.`
        }
      />
    </Dialog>
  )
}
