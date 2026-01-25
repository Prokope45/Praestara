import {
  Container,
  Typography,
  Box,
  Button,
  Paper,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Chip,
} from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import { useCallback, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { FiSave, FiPlus, FiEdit2, FiTrash } from "react-icons/fi"
import { Radar } from "react-chartjs-2"
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js"
import type { OrientationPublic, OrientationTrait } from "../../types/orientations"
import type { OrientationUpdate } from "../../client"
import { OrientationsService } from "../../client"
import type { ApiError } from "../../client/core/ApiError"
import useCustomToast from "../../hooks/useCustomToast"
import { handleError } from "../../utils"
import TraitModal from "./TraitModal"

// Register Chart.js components
ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

interface EditableOrientationProps {
  orientation: OrientationPublic
}

const EditableOrientation = ({ orientation }: EditableOrientationProps) => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<"add" | "edit">("add")
  const [selectedTrait, setSelectedTrait] = useState<OrientationTrait | null>(null)
  const [traits, setTraits] = useState<OrientationTrait[]>(orientation.traits || [])
  const [formData, setFormData] = useState({
    title: orientation.title,
    description: orientation.description || "",
    notes: orientation.notes || "",
  })

  const updateMutation = useMutation({
    mutationFn: (data: OrientationUpdate) =>
      OrientationsService.updateOrientationEndpoint({ id: orientation.id, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Orientation updated successfully.")
      // Navigate back to view mode
      navigate({
        to: "/orientations",
        search: { orientationId: orientation.id },
      })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["orientations"] })
      queryClient.invalidateQueries({ queryKey: ["orientation", orientation.id] })
    },
  })

  const handleAddTrait = () => {
    setSelectedTrait(null)
    setModalMode("add")
    setModalOpen(true)
  }

  const handleEditTrait = (trait: OrientationTrait) => {
    setSelectedTrait(trait)
    setModalMode("edit")
    setModalOpen(true)
  }

  const handleDeleteTrait = (traitId: string) => {
    setTraits((prev) => prev.filter((t) => t.id !== traitId))
  }

  const handleSaveTrait = useCallback(
    (traitData: Partial<OrientationTrait>) => {
      if (modalMode === "add") {
        // Add new trait
        const newId = `trait-${Date.now()}`
        const newTrait: OrientationTrait = {
          id: newId,
          name: traitData.name!,
          value: traitData.value!,
          description: traitData.description,
        }
        setTraits((prev) => [...prev, newTrait])
      } else if (modalMode === "edit" && traitData.id) {
        // Update existing trait
        setTraits((prev) =>
          prev.map((trait) =>
            trait.id === traitData.id ? ({ ...trait, ...traitData } as OrientationTrait) : trait
          )
        )
      }
    },
    [modalMode]
  )

  const handleSave = useCallback(() => {
    const orientationData: OrientationUpdate = {
      title: formData.title,
      description: formData.description || undefined,
      notes: formData.notes || undefined,
      traits: traits.map(trait => ({
        name: trait.name,
        value: trait.value,
        description: trait.description,
      })),
    }

    updateMutation.mutate(orientationData)
  }, [formData, traits, updateMutation])

  const handleCancel = useCallback(() => {
    navigate({
      to: "/orientations",
      search: { orientationId: orientation.id },
    })
  }, [navigate, orientation.id])

  // Prepare radar chart data
  const chartData = {
    labels: traits.map((trait) => trait.name),
    datasets: [
      {
        label: "Current Level",
        data: traits.map((trait) => trait.value),
        backgroundColor: "rgba(25, 118, 210, 0.2)",
        borderColor: "rgba(25, 118, 210, 1)",
        borderWidth: 2,
        pointBackgroundColor: "rgba(25, 118, 210, 1)",
        pointBorderColor: "#fff",
        pointHoverBackgroundColor: "#fff",
        pointHoverBorderColor: "rgba(25, 118, 210, 1)",
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        min: 0,
        ticks: {
          stepSize: 20,
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            return `${context.label}: ${context.parsed.r}%`
          },
        },
      },
    },
  }

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h4" component="h1">
            Edit Orientation
          </Typography>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button variant="outlined" onClick={handleCancel} disabled={updateMutation.isPending}>
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={<FiSave />}
              onClick={handleSave}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </Box>
        </Box>


        {/* Basic Information */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Basic Information
          </Typography>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              label="Title"
              value={formData.title}
              onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
              required
              fullWidth
              placeholder="e.g., 'I want to be a friendlier person'"
            />
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              multiline
              rows={3}
              fullWidth
              placeholder="Describe your aspiration"
            />
          </Box>
        </Paper>

        {/* Traits Management */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
            <Typography variant="h6">Traits</Typography>
            <Button variant="contained" size="small" startIcon={<FiPlus />} onClick={handleAddTrait}>
              Add Trait
            </Button>
          </Box>

          {traits.length > 0 ? (
            <List>
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
                        <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
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
              No traits added yet. Click "Add Trait" to get started.
            </Typography>
          )}
        </Paper>

        {/* Radar Chart Preview */}
        {traits.length > 0 && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Preview
            </Typography>
            <Box
              sx={{
                maxWidth: 600,
                mx: "auto",
                height: 400,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Radar data={chartData} options={chartOptions} />
            </Box>
          </Paper>
        )}

        {/* Reflections/Notes */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Reflections
          </Typography>
          <TextField
            label="Personal Notes"
            value={formData.notes}
            onChange={(e) => setFormData((prev) => ({ ...prev, notes: e.target.value }))}
            multiline
            rows={5}
            fullWidth
            placeholder="Reflect on your progress, challenges, and insights..."
          />
        </Paper>

        <Button variant="outlined" onClick={handleCancel}>
          Cancel
        </Button>

        {/* Trait Modal */}
        <TraitModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          onSave={handleSaveTrait}
          trait={selectedTrait}
          mode={modalMode}
        />
      </Box>
    </Container>
  )
}

export default EditableOrientation
