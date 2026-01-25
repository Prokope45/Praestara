import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Slider,
  Typography,
} from "@mui/material"
import { useState, useEffect } from "react"
import type { OrientationTrait } from "../../types/orientations"

interface TraitModalProps {
  open: boolean
  onClose: () => void
  onSave: (trait: Partial<OrientationTrait>) => void
  trait?: OrientationTrait | null
  mode: "add" | "edit"
}

const TraitModal = ({ open, onClose, onSave, trait, mode }: TraitModalProps) => {
  const [formData, setFormData] = useState({
    name: "",
    value: 50,
    description: "",
  })

  useEffect(() => {
    if (trait && mode === "edit") {
      setFormData({
        name: trait.name,
        value: trait.value,
        description: trait.description || "",
      })
    } else {
      // Reset form for add mode
      setFormData({
        name: "",
        value: 50,
        description: "",
      })
    }
  }, [trait, mode, open])

  const handleSubmit = () => {
    const traitData: Partial<OrientationTrait> = {
      ...formData,
    }

    if (trait && mode === "edit") {
      traitData.id = trait.id
    }

    onSave(traitData)
    onClose()
  }

  const handleChange = (field: string, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{mode === "add" ? "Add New Trait" : "Edit Trait"}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3, mt: 2 }}>
          <TextField
            label="Trait Name"
            value={formData.name}
            onChange={(e) => handleChange("name", e.target.value)}
            required
            fullWidth
            placeholder="e.g., Patience, Empathy, Research Skills"
          />

          <TextField
            label="Description"
            value={formData.description}
            onChange={(e) => handleChange("description", e.target.value)}
            multiline
            rows={2}
            fullWidth
            placeholder="What does this trait mean to you?"
          />

          <Box>
            <Typography variant="body2" sx={{ mb: 1 }}>
              Current Level: {formData.value}%
            </Typography>
            <Slider
              value={formData.value}
              onChange={(_, value) => handleChange("value", value as number)}
              min={0}
              max={100}
              step={5}
              marks={[
                { value: 0, label: "0%" },
                { value: 25, label: "25%" },
                { value: 50, label: "50%" },
                { value: 75, label: "75%" },
                { value: 100, label: "100%" },
              ]}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
              Rate your current level in this trait (0-100%)
            </Typography>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!formData.name.trim()}
        >
          {mode === "add" ? "Add Trait" : "Save Changes"}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default TraitModal
