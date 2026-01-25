import { Container, Typography, Box, Button, Paper, Chip } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import { useCallback, useMemo } from "react"
import { FiEdit } from "react-icons/fi"
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
import type { OrientationPublic } from "../../types/orientations"

// Register Chart.js components
ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

interface OrientationDetailProps {
  orientation: OrientationPublic
}

const OrientationDetail = ({ orientation }: OrientationDetailProps) => {
  const navigate = useNavigate()

  // Calculate metrics
  const metrics = useMemo(() => {
    const totalTraits = orientation.traits?.length || 0
    const averageValue =
      totalTraits > 0
        ? Math.round(
            (orientation.traits?.reduce((sum, trait) => sum + trait.value, 0) || 0) / totalTraits
          )
        : 0

    const sortedTraits = [...(orientation.traits || [])].sort((a, b) => b.value - a.value)
    const highestTrait = sortedTraits[0] || null
    const lowestTrait = sortedTraits[sortedTraits.length - 1] || null

    return {
      totalTraits,
      averageValue,
      highestTrait,
      lowestTrait,
    }
  }, [orientation.traits])

  // Prepare radar chart data
  const chartData = useMemo(() => {
    return {
      labels: orientation.traits?.map((trait) => trait.name) || [],
      datasets: [
        {
          label: "Current Level",
          data: orientation.traits?.map((trait) => trait.value) || [],
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
  }, [orientation.traits])

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

  const handleEdit = useCallback(() => {
    navigate({
      to: "/orientations",
      search: { orientationId: orientation.id, editMode: "true" },
    })
  }, [navigate, orientation.id])

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h4" component="h1">
            {orientation.title}
          </Typography>
          <Button variant="outlined" startIcon={<FiEdit />} onClick={handleEdit}>
            Edit
          </Button>
        </Box>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {orientation.description || "No description"}
        </Typography>

        {/* Metrics */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Overview
          </Typography>
          <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Total Traits
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: "bold" }}>
                {metrics.totalTraits}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Average Level
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: "bold", color: "primary.main" }}>
                {metrics.averageValue}%
              </Typography>
            </Box>
            {metrics.highestTrait && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Strongest Trait
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
                  <Typography variant="h6" sx={{ fontWeight: "bold" }}>
                    {metrics.highestTrait.name}
                  </Typography>
                  <Chip
                    label={`${metrics.highestTrait.value}%`}
                    size="small"
                    color="success"
                  />
                </Box>
              </Box>
            )}
            {metrics.lowestTrait && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Growth Area
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
                  <Typography variant="h6" sx={{ fontWeight: "bold" }}>
                    {metrics.lowestTrait.name}
                  </Typography>
                  <Chip label={`${metrics.lowestTrait.value}%`} size="small" color="warning" />
                </Box>
              </Box>
            )}
          </Box>
        </Paper>

        {/* Radar Chart */}
        {(orientation.traits?.length || 0) > 0 ? (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Trait Visualization
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
        ) : (
          <Paper sx={{ p: 3, mb: 3, textAlign: "center" }}>
            <Typography variant="body1" color="text.secondary">
              No traits added yet. Click "Edit" to add traits to this orientation.
            </Typography>
          </Paper>
        )}

        {/* Traits List */}
        {(orientation.traits?.length || 0) > 0 && (
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Traits Details
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {orientation.traits?.map((trait) => (
                <Box
                  key={trait.id}
                  sx={{
                    p: 2,
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 1,
                  }}
                >
                  <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                      {trait.name}
                    </Typography>
                    <Chip label={`${trait.value}%`} size="small" color="primary" />
                  </Box>
                  {trait.description && (
                    <Typography variant="body2" color="text.secondary">
                      {trait.description}
                    </Typography>
                  )}
                </Box>
              ))}
            </Box>
          </Paper>
        )}

        {/* Notes */}
        {orientation.notes && (
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              Reflections
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
              {orientation.notes}
            </Typography>
          </Paper>
        )}

        <Button variant="outlined" onClick={() => navigate({ to: "/orientations" })}>
          Back to Orientations
        </Button>
      </Box>
    </Container>
  )
}

export default OrientationDetail
