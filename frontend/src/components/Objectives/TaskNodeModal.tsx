import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  FormControl,
  FormLabel,
  Box,
} from "@mui/material"
import { useState, useEffect } from "react"
import { TaskPriority, type TaskNode } from "../../types/objectives"

interface TaskNodeModalProps {
  open: boolean
  onClose: () => void
  onSave: (task: Partial<TaskNode>) => void
  task?: TaskNode | null
  mode: "add" | "edit"
}

const TaskNodeModal = ({ open, onClose, onSave, task, mode }: TaskNodeModalProps) => {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    deadline: "",
    priority: TaskPriority.MEDIUM,
    isActive: true,
  })

  useEffect(() => {
    if (task && mode === "edit") {
      setFormData({
        title: task.title,
        description: task.description,
        deadline: task.deadline.split("T")[0], // Convert ISO to date input format
        priority: task.priority,
        isActive: task.isActive,
      })
    } else {
      // Reset form for add mode
      setFormData({
        title: "",
        description: "",
        deadline: new Date().toISOString().split("T")[0],
        priority: TaskPriority.MEDIUM,
        isActive: true,
      })
    }
  }, [task, mode, open])

  const handleSubmit = () => {
    const taskData: Partial<TaskNode> = {
      ...formData,
      deadline: new Date(formData.deadline).toISOString(),
    }

    if (task && mode === "edit") {
      taskData.id = task.id
      taskData.position = task.position
    }

    onSave(taskData)
    onClose()
  }

  const handleChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{mode === "add" ? "Add New Task" : "Edit Task"}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 2 }}>
          <TextField
            label="Title"
            value={formData.title}
            onChange={(e) => handleChange("title", e.target.value)}
            required
            fullWidth
          />

          <TextField
            label="Description"
            value={formData.description}
            onChange={(e) => handleChange("description", e.target.value)}
            multiline
            rows={3}
            fullWidth
          />

          <TextField
            label="Deadline"
            type="date"
            value={formData.deadline}
            onChange={(e) => handleChange("deadline", e.target.value)}
            InputLabelProps={{ shrink: true }}
            required
            fullWidth
          />

          <TextField
            label="Priority"
            select
            value={formData.priority}
            onChange={(e) => handleChange("priority", e.target.value)}
            fullWidth
          >
            <MenuItem value={TaskPriority.LOW}>Low</MenuItem>
            <MenuItem value={TaskPriority.MEDIUM}>Medium</MenuItem>
            <MenuItem value={TaskPriority.HIGH}>High</MenuItem>
            <MenuItem value={TaskPriority.CRITICAL}>Critical</MenuItem>
          </TextField>

          <FormControl>
            <FormLabel>Status</FormLabel>
            <TextField
              select
              value={formData.isActive ? "active" : "completed"}
              onChange={(e) => handleChange("isActive", e.target.value === "active")}
              fullWidth
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
            </TextField>
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!formData.title || !formData.deadline}
        >
          {mode === "add" ? "Add Task" : "Save Changes"}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default TaskNodeModal
