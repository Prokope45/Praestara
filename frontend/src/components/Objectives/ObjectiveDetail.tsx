import { Container, Typography, Box, Button, Chip, Paper } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import { useCallback, useMemo } from "react"
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from "reactflow"
import "reactflow/dist/style.css"
import { FiEdit } from "react-icons/fi"
import type { ObjectivePublic, TaskPriority } from "../../types/objectives"

interface ObjectiveDetailProps {
  objective: ObjectivePublic
}

const getPriorityColor = (priority: TaskPriority): string => {
  switch (priority) {
    case "critical":
      return "#d32f2f"
    case "high":
      return "#f57c00"
    case "medium":
      return "#fbc02d"
    case "low":
      return "#388e3c"
    default:
      return "#757575"
  }
}

const ObjectiveDetail = ({ objective }: ObjectiveDetailProps) => {
  const navigate = useNavigate()

  // Calculate metrics
  const metrics = useMemo(() => {
    const totalTasks = objective.tasks.length
    const completedTasks = objective.tasks.filter((task) => !task.isActive).length
    const activeTasks = objective.tasks.filter((task) => task.isActive).length
    const percentComplete = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

    return {
      totalTasks,
      completedTasks,
      activeTasks,
      percentComplete,
    }
  }, [objective.tasks])

  // Convert tasks to ReactFlow nodes
  const initialNodes: Node[] = useMemo(
    () =>
      objective.tasks.map((task) => ({
        id: task.id,
        type: "default",
        position: task.position,
        data: {
          label: (
            <Box sx={{ p: 1, minWidth: 150 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: "bold", mb: 0.5 }}>
                {task.title}
              </Typography>
              <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mt: 1 }}>
                <Chip
                  label={task.priority.toUpperCase()}
                  size="small"
                  sx={{
                    backgroundColor: getPriorityColor(task.priority),
                    color: "white",
                    fontSize: "0.65rem",
                    height: 18,
                  }}
                />
                <Chip
                  label={new Date(task.deadline).toLocaleDateString()}
                  size="small"
                  sx={{ fontSize: "0.65rem", height: 18 }}
                />
              </Box>
            </Box>
          ),
        },
        style: {
          background: task.isActive ? "#ffffff" : "#e0e0e0",
          border: task.isActive ? "2px solid #1976d2" : "2px solid #9e9e9e",
          borderRadius: 8,
          opacity: task.isActive ? 1 : 0.6,
          padding: 0,
        },
      })),
    [objective.tasks]
  )

  // Convert edges to ReactFlow edges
  const initialEdges: Edge[] = useMemo(
    () =>
      objective.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: "smoothstep",
        animated: true,
        style: { stroke: "#1976d2", strokeWidth: 2 },
      })),
    [objective.edges]
  )

  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  const handleEdit = useCallback(() => {
    navigate({
      to: "/tasks",
      search: { objectiveId: objective.id, editMode: "true" },
    })
  }, [navigate, objective.id])

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h4" component="h1">
            {objective.title}
          </Typography>
          <Button variant="outlined" startIcon={<FiEdit />} onClick={handleEdit}>
            Edit
          </Button>
        </Box>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {objective.description || "No description"}
        </Typography>

        {/* Metrics */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Progress
          </Typography>
          <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Completion
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: "bold", color: "primary.main" }}>
                {metrics.completedTasks} / {metrics.totalTasks} tasks ({metrics.percentComplete}%)
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Active Tasks
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: "bold" }}>
                {metrics.activeTasks}
              </Typography>
            </Box>
          </Box>
        </Paper>

        {/* ReactFlow Graph */}
        <Paper sx={{ height: 600, mb: 3 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            attributionPosition="bottom-left"
          >
            <Background />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const task = objective.tasks.find((t) => t.id === node.id)
                return task?.isActive ? "#1976d2" : "#9e9e9e"
              }}
            />
          </ReactFlow>
        </Paper>

        <Button
          variant="outlined"
          onClick={() => navigate({ to: "/tasks" })}
        >
          Back to Objectives
        </Button>
      </Box>
    </Container>
  )
}

export default ObjectiveDetail
