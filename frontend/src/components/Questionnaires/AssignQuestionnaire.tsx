import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Stack,
  Typography,
  Chip,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { FiUser, FiCalendar } from "react-icons/fi"

import { QuestionnairesService, UsersService, type QuestionnaireTemplatePublic } from "../../client"
import { Button } from "../ui/button"
import useCustomToast from "../../hooks/useCustomToast"

interface AssignQuestionnaireProps {
  open: boolean
  onClose: () => void
  questionnaire: QuestionnaireTemplatePublic
}

export function AssignQuestionnaire({ open, onClose, questionnaire }: AssignQuestionnaireProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const [selectedUserId, setSelectedUserId] = useState("")
  const [dueDate, setDueDate] = useState("")

  // Fetch all users
  const { data: usersData } = useQuery({
    queryKey: ["users"],
    queryFn: () => UsersService.readUsers({ skip: 0, limit: 1000 }),
    enabled: open,
  })

  const assignMutation = useMutation({
    mutationFn: (data: any) =>
      QuestionnairesService.createAssignment({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Questionnaire assigned successfully")
      queryClient.invalidateQueries({ queryKey: ["questionnaire-assignments"] })
      handleClose()
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to assign questionnaire")
    },
  })

  const handleClose = () => {
    setSelectedUserId("")
    setDueDate("")
    onClose()
  }

  const handleSubmit = () => {
    if (!selectedUserId) {
      showErrorToast("Please select a user")
      return
    }

    assignMutation.mutate({
      questionnaire_id: questionnaire.id,
      user_id: selectedUserId,
      due_date: dueDate || null,
    })
  }

  // Get minimum date (today)
  const today = new Date().toISOString().split("T")[0]

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Assign Questionnaire</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 2 }}>
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
              <Box sx={{ mt: 1 }}>
                <Chip
                  label={`${questionnaire.questions?.length || 0} questions`}
                  size="small"
                  variant="outlined"
                />
              </Box>
            </Box>
          </Box>

          <FormControl fullWidth required>
            <InputLabel>Select User</InputLabel>
            <Select
              value={selectedUserId}
              label="Select User"
              onChange={(e) => setSelectedUserId(e.target.value)}
              startAdornment={<FiUser style={{ marginRight: 8, color: "#666" }} />}
            >
              {usersData?.data?.map((user) => (
                <MenuItem key={user.id} value={user.id}>
                  <Box>
                    <Typography variant="body2">
                      {user.full_name || "No name"}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {user.email}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Due Date (Optional)"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            InputLabelProps={{
              shrink: true,
            }}
            inputProps={{
              min: today,
            }}
            InputProps={{
              startAdornment: <FiCalendar style={{ marginRight: 8, color: "#666" }} />,
            }}
            helperText="Leave empty for no due date"
            fullWidth
          />

          <Box
            sx={{
              p: 2,
              bgcolor: "info.lighter",
              borderRadius: 1,
              border: "1px solid",
              borderColor: "info.light",
            }}
          >
            <Typography variant="caption" color="info.dark">
              <strong>Note:</strong> The user will be notified and can access the questionnaire
              from their Questionnaires page.
            </Typography>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={assignMutation.isPending}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          loading={assignMutation.isPending}
          disabled={assignMutation.isPending || !selectedUserId}
        >
          Assign
        </Button>
      </DialogActions>
    </Dialog>
  )
}
