import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from "@mui/material"
import { useState } from "react"
import { useNavigate } from "@tanstack/react-router"
import { FiPlus, FiAlertCircle } from "react-icons/fi"
import type { ObjectivePublic } from "../../types/objectives"
import { saveTempObjective } from "../../utils/tempObjectiveStorage"

const AddObjective = () => {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [formData, setFormData] = useState({
    title: "",
    description: "",
  })

  const handleOpen = () => setOpen(true)
  const handleClose = () => {
    setOpen(false)
    setFormData({ title: "", description: "" })
  }

  const handleSubmit = () => {
    if (!formData.title.trim()) return

    const newObjective: ObjectivePublic = {
      id: `temp-${Date.now()}`,
      title: formData.title,
      description: formData.description,
      tasks: [],
      edges: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    // Save to temporary storage
    saveTempObjective(newObjective)

    // Navigate to edit mode for the new objective
    navigate({
      to: "/tasks",
      search: { objectiveId: newObjective.id, editMode: "true" },
    })

    handleClose()
  }

  return (
    <>
      <Box sx={{ mt: 3, mb: 2 }}>
        <Button
          variant="contained"
          color="primary"
          startIcon={<FiPlus />}
          onClick={handleOpen}
        >
          Add Objective
        </Button>
      </Box>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Objective</DialogTitle>
        <DialogContent>
          <Alert severity="info" icon={<FiAlertCircle />} sx={{ mb: 2, mt: 1 }}>
            <strong>Temporary Storage:</strong> This objective will be saved in your browser's
            localStorage only. Data will be lost if you clear browser data.
          </Alert>

          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              label="Title"
              value={formData.title}
              onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
              required
              fullWidth
              autoFocus
            />

            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              multiline
              rows={3}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.title.trim()}
          >
            Create & Edit
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default AddObjective
