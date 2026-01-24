import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
} from "@mui/material"
import { useState } from "react"
import { useNavigate } from "@tanstack/react-router"
import { FiPlus, FiAlertCircle, FiEdit2, FiTrash } from "react-icons/fi"
import type { OrientationPublic, OrientationTrait } from "../../types/orientations"
import { saveTempOrientation } from "../../utils/tempOrientationStorage"
import TraitModal from "./TraitModal"

const AddOrientation = () => {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [traitModalOpen, setTraitModalOpen] = useState(false)
  const [traitModalMode, setTraitModalMode] = useState<"add" | "edit">("add")
  const [selectedTrait, setSelectedTrait] = useState<OrientationTrait | null>(null)
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    notes: "",
  })
  const [traits, setTraits] = useState<OrientationTrait[]>([])

  const handleOpen = () => setOpen(true)
  const handleClose = () => {
    setOpen(false)
    setFormData({ title: "", description: "", notes: "" })
    setTraits([])
  }

  const handleAddTrait = () => {
    setSelectedTrait(null)
    setTraitModalMode("add")
    setTraitModalOpen(true)
  }

  const handleEditTrait = (trait: OrientationTrait) => {
    setSelectedTrait(trait)
    setTraitModalMode("edit")
    setTraitModalOpen(true)
  }

  const handleDeleteTrait = (traitId: string) => {
    setTraits((prev) => prev.filter((t) => t.id !== traitId))
  }

  const handleSaveTrait = (traitData: Partial<OrientationTrait>) => {
    if (traitModalMode === "add") {
      const newId = `trait-${Date.now()}`
      const newTrait: OrientationTrait = {
        id: newId,
        name: traitData.name!,
        value: traitData.value!,
        description: traitData.description,
      }
      setTraits((prev) => [...prev, newTrait])
    } else if (traitModalMode === "edit" && traitData.id) {
      setTraits((prev) =>
        prev.map((trait) =>
          trait.id === traitData.id ? ({ ...trait, ...traitData } as OrientationTrait) : trait
        )
      )
    }
  }

  const handleSubmit = () => {
    if (!formData.title.trim()) return

    const newOrientation: OrientationPublic = {
      id: `temp-${Date.now()}`,
      title: formData.title,
      description: formData.description,
      traits: traits,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      notes: formData.notes,
    }

    // Save to temporary storage
    saveTempOrientation(newOrientation)

    // Navigate to view mode for the new orientation
    navigate({
      to: "/orientations",
      search: { orientationId: newOrientation.id },
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
          Add Orientation
        </Button>
      </Box>

      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>Create New Orientation</DialogTitle>
        <DialogContent>
          <Alert severity="info" icon={<FiAlertCircle />} sx={{ mb: 3, mt: 1 }}>
            <strong>Temporary Storage:</strong> This orientation will be saved in your browser's
            localStorage only. Data will be lost if you clear browser data.
          </Alert>

          <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
            {/* Basic Information */}
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: "bold", mb: 2 }}>
                Basic Information
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <TextField
                  label="Title (e.g., 'I want to be a great father')"
                  value={formData.title}
                  onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
                  required
                  fullWidth
                  autoFocus
                  placeholder="Who do you want to be?"
                />

                <TextField
                  label="Description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, description: e.target.value }))
                  }
                  multiline
                  rows={3}
                  fullWidth
                  placeholder="Describe your aspiration and what it means to you"
                />
              </Box>
            </Box>

            <Divider />

            {/* Traits */}
            <Box>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                  Traits
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<FiPlus />}
                  onClick={handleAddTrait}
                >
                  Add Trait
                </Button>
              </Box>

              {traits.length > 0 ? (
                <List sx={{ maxHeight: 200, overflow: "auto" }}>
                  {traits.map((trait) => (
                    <ListItem
                      key={trait.id}
                      sx={{
                        border: "1px solid",
                        borderColor: "divider",
                        borderRadius: 1,
                        mb: 1,
                      }}
                      secondaryAction={
                        <Box sx={{ display: "flex", gap: 1 }}>
                          <IconButton size="small" onClick={() => handleEditTrait(trait)}>
                            <FiEdit2 />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteTrait(trait.id)}
                          >
                            <FiTrash />
                          </IconButton>
                        </Box>
                      }
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                            <Typography variant="body1" sx={{ fontWeight: "bold" }}>
                              {trait.name}
                            </Typography>
                            <Chip label={`${trait.value}%`} size="small" color="primary" />
                          </Box>
                        }
                        secondary={trait.description}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 2 }}>
                  No traits added yet. Click "Add Trait" to define the qualities that make up this
                  orientation.
                </Typography>
              )}
            </Box>

            <Divider />

            {/* Reflections */}
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: "bold", mb: 2 }}>
                Reflections (Optional)
              </Typography>
              <TextField
                label="Personal Notes"
                value={formData.notes}
                onChange={(e) => setFormData((prev) => ({ ...prev, notes: e.target.value }))}
                multiline
                rows={4}
                fullWidth
                placeholder="Reflect on your aspirations, challenges, and insights..."
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={!formData.title.trim()}>
            Create Orientation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Trait Modal */}
      <TraitModal
        open={traitModalOpen}
        onClose={() => setTraitModalOpen(false)}
        onSave={handleSaveTrait}
        trait={selectedTrait}
        mode={traitModalMode}
      />
    </>
  )
}

export default AddOrientation
