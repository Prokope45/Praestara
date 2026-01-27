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
  Checkbox,
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

  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([])
  const [dueDate, setDueDate] = useState("")

  // Fetch all users
  const { data: usersData } = useQuery({
    queryKey: ["users"],
    queryFn: () => UsersService.readUsers({ skip: 0, limit: 1000 }),
    enabled: open,
  })

  // Fetch existing assignments for this questionnaire to show which users are already assigned
  const { data: existingAssignments } = useQuery({
    queryKey: ["all-assignments", questionnaire.id],
    queryFn: async () => {
      const response = await QuestionnairesService.readAllAssignments({ 
        questionnaireId: questionnaire.id,
        skip: 0, 
        limit: 1000 
      })
      return response.data.filter((a: any) => a.status === "PENDING")
    },
    enabled: open,
  })

  // Create a Set of user IDs who already have pending assignments
  const assignedUserIds = new Set(
    existingAssignments?.map((assignment: any) => assignment.user_id) || []
  )

  // Check if a user is already assigned
  const isUserAssigned = (userId: string) => assignedUserIds.has(userId)

  const assignMutation = useMutation({
    mutationFn: (data: any) =>
      QuestionnairesService.createBulkAssignments({ requestBody: data }),
    onSuccess: (data: any) => {
      const count = data.count || selectedUserIds.length
      showSuccessToast(`Questionnaire assigned to ${count} user(s) successfully`)
      queryClient.invalidateQueries({ queryKey: ["questionnaire-assignments"] })
      handleClose()
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to assign questionnaire")
    },
  })

  const handleClose = () => {
    setSelectedUserIds([])
    setDueDate("")
    onClose()
  }

  const handleSubmit = () => {
    if (selectedUserIds.length === 0) {
      showErrorToast("Please select at least one user")
      return
    }

    assignMutation.mutate({
      questionnaire_id: questionnaire.id,
      user_ids: selectedUserIds,
      due_date: dueDate || null,
    })
  }

  const handleSelectAll = () => {
    if (usersData?.data) {
      setSelectedUserIds(usersData.data.map((user) => user.id))
    }
  }

  const handleClearAll = () => {
    setSelectedUserIds([])
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

          <Box>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Select Users *
              </Typography>
              <Stack direction="row" spacing={1}>
                <Button
                  size="small"
                  variant="text"
                  onClick={handleSelectAll}
                  disabled={!usersData?.data || usersData.data.length === 0}
                >
                  Select All
                </Button>
                <Button
                  size="small"
                  variant="text"
                  onClick={handleClearAll}
                  disabled={selectedUserIds.length === 0}
                >
                  Clear
                </Button>
              </Stack>
            </Stack>
            
            <FormControl fullWidth required>
              <InputLabel>Select Users</InputLabel>
              <Select
                multiple
                value={selectedUserIds}
                label="Select Users"
                onChange={(e) => setSelectedUserIds(typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value)}
                startAdornment={<FiUser style={{ marginRight: 8, color: "#666" }} />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => {
                      const user = usersData?.data?.find((u) => u.id === value)
                      return (
                        <Chip
                          key={value}
                          label={user?.full_name || user?.email || value}
                          size="small"
                        />
                      )
                    })}
                  </Box>
                )}
              >
                {usersData?.data?.map((user) => {
                  const alreadyAssigned = isUserAssigned(user.id)
                  return (
                    <MenuItem key={user.id} value={user.id}>
                      <Checkbox checked={selectedUserIds.indexOf(user.id) > -1} />
                      <Box sx={{ ml: 1, flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="body2">
                            {user.full_name || "No name"}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {user.email}
                          </Typography>
                        </Box>
                        {alreadyAssigned && (
                          <Chip
                            label="Already Assigned"
                            size="small"
                            color="warning"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                    </MenuItem>
                  )
                })}
              </Select>
            </FormControl>
            
            {selectedUserIds.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  {selectedUserIds.length} user(s) selected
                </Typography>
                {selectedUserIds.some(id => isUserAssigned(id)) && (
                  <Typography variant="caption" color="warning.main" sx={{ display: 'block', mt: 0.5 }}>
                    ⚠️ Warning: {selectedUserIds.filter(id => isUserAssigned(id)).length} selected user(s) already have pending assignments
                  </Typography>
                )}
              </Box>
            )}
          </Box>

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
          disabled={assignMutation.isPending || selectedUserIds.length === 0}
        >
          Assign to {selectedUserIds.length} User{selectedUserIds.length !== 1 ? 's' : ''}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
