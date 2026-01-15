import { Container, Typography, Box, Button, Chip, Paper, IconButton, Alert } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import { useCallback, useMemo, useState, useEffect } from "react"
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeProps,
  Handle,
  Position,
} from "reactflow"
import "reactflow/dist/style.css"
import { FiSave, FiPlus, FiEdit2, FiAlertCircle } from "react-icons/fi"
import type { ObjectivePublic, TaskPriority, TaskNode, TaskEdge } from "../../types/objectives"
import TaskNodeModal from "./TaskNodeModal"
import { saveTempObjective } from "../../utils/tempObjectiveStorage"

interface EditableObjectiveProps {
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

// Custom node component with edit button and connection handles
const CustomNode = ({ data, id }: NodeProps) => {
  return (
    <Box sx={{ position: "relative" }}>
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#555' }}
      />
      {data.label}
      <IconButton
        size="small"
        sx={{
          position: "absolute",
          top: 2,
          right: 2,
          backgroundColor: "white",
          "&:hover": { backgroundColor: "grey.100" },
          padding: "2px",
        }}
        onClick={() => data.onEdit(id)}
      >
        <FiEdit2 size={12} />
      </IconButton>
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#555' }}
      />
    </Box>
  )
}

const nodeTypes = {
  custom: CustomNode,
}

const EditableObjective = ({ objective }: EditableObjectiveProps) => {
  const navigate = useNavigate()
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<"add" | "edit">("add")
  const [selectedTask, setSelectedTask] = useState<TaskNode | null>(null)
  const [taskMap, setTaskMap] = useState<Map<string, TaskNode>>(
    new Map(objective.tasks.map((task) => [task.id, task]))
  )

  // Calculate metrics
  const metrics = useMemo(() => {
    const tasks = Array.from(taskMap.values())
    const totalTasks = tasks.length
    const completedTasks = tasks.filter((task) => !task.isActive).length
    const activeTasks = tasks.filter((task) => task.isActive).length
    const percentComplete = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

    return {
      totalTasks,
      completedTasks,
      activeTasks,
      percentComplete,
    }
  }, [taskMap])

  // Use a stable reference that doesn't depend on taskMap
  const handleEditNode = useCallback((nodeId: string) => {
    setTaskMap((currentTaskMap) => {
      const task = currentTaskMap.get(nodeId)
      if (task) {
        setSelectedTask(task)
        setModalMode("edit")
        setModalOpen(true)
      }
      return currentTaskMap
    })
  }, [])

  // Convert tasks to ReactFlow nodes - memoize the function itself
  const createNodeFromTask = useCallback((task: TaskNode, onEdit: (id: string) => void) => ({
    id: task.id,
    type: "custom",
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
      onEdit,
    },
    style: {
      background: task.isActive ? "#ffffff" : "#e0e0e0",
      border: task.isActive ? "2px solid #1976d2" : "2px solid #9e9e9e",
      borderRadius: 8,
      opacity: task.isActive ? 1 : 0.6,
      padding: 0,
    },
  }), [])

  const initialNodes: Node[] = useMemo(
    () => objective.tasks.map((task) => createNodeFromTask(task, handleEditNode)),
    [objective.tasks, createNodeFromTask, handleEditNode]
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

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  // Handle edge deletion with Delete/Backspace key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Delete' || event.key === 'Backspace') {
        setEdges((eds) => eds.filter((edge) => !edge.selected))
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [setEdges])

  const handleAddNode = () => {
    setSelectedTask(null)
    setModalMode("add")
    setModalOpen(true)
  }

  const handleSaveTask = useCallback((taskData: Partial<TaskNode>) => {
    if (modalMode === "add") {
      // Add new task
      const newId = `task-${Date.now()}`
      const newTask: TaskNode = {
        id: newId,
        title: taskData.title!,
        description: taskData.description!,
        deadline: taskData.deadline!,
        priority: taskData.priority!,
        isActive: taskData.isActive!,
        position: { x: 250, y: 250 }, // Default position
      }

      setTaskMap((prev) => new Map(prev).set(newId, newTask))
      setNodes((nds) => [...nds, createNodeFromTask(newTask, handleEditNode)])
    } else if (modalMode === "edit" && taskData.id) {
      // Update existing task - preserve position from current node
      const currentNode = nodes.find(n => n.id === taskData.id)
      const updatedTask: TaskNode = {
        ...taskMap.get(taskData.id)!,
        ...taskData,
        position: currentNode?.position || taskData.position || { x: 0, y: 0 },
      } as TaskNode

      setTaskMap((prev) => new Map(prev).set(taskData.id!, updatedTask))
      
      // Update only the data and style properties, preserve everything else including position
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === taskData.id) {
            const newNodeData = createNodeFromTask(updatedTask, handleEditNode)
            return {
              ...node,
              data: newNodeData.data,
              style: newNodeData.style,
            }
          }
          return node
        })
      )
    }
  }, [modalMode, taskMap, createNodeFromTask, setNodes, nodes, handleEditNode])

  const handleSave = useCallback(() => {
    // Convert ReactFlow edges back to TaskEdge format
    const taskEdges: TaskEdge[] = edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
    }))

    // Update node positions from ReactFlow
    const updatedTasks = nodes.map((node) => {
      const task = taskMap.get(node.id)
      return task ? { ...task, position: node.position } : null
    }).filter((task): task is TaskNode => task !== null)

    // Create updated objective
    const updatedObjective: ObjectivePublic = {
      ...objective,
      tasks: updatedTasks,
      edges: taskEdges,
      updatedAt: new Date().toISOString(),
    }

    // Save to temporary storage
    saveTempObjective(updatedObjective)
    
    console.log("Saved objective to temporary storage", updatedObjective)

    // Navigate back to view mode
    navigate({
      to: "/tasks",
      search: { objectiveId: objective.id },
    })
  }, [navigate, objective, nodes, edges, taskMap])

  const handleCancel = useCallback(() => {
    navigate({
      to: "/tasks",
      search: { objectiveId: objective.id },
    })
  }, [navigate, objective.id])

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h4" component="h1">
            Edit: {objective.title}
          </Typography>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button variant="outlined" onClick={handleCancel}>
              Cancel
            </Button>
            <Button variant="contained" startIcon={<FiSave />} onClick={handleSave}>
              Save
            </Button>
          </Box>
        </Box>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {objective.description || "No description"}
        </Typography>

        {/* Temporary Storage Warning */}
        {objective.id.startsWith("temp-") && (
          <Alert severity="warning" icon={<FiAlertCircle />} sx={{ mb: 3 }}>
            <strong>Temporary Storage:</strong> This objective is stored in your browser's localStorage only. 
            Changes will be lost if you clear browser data. This is for demonstration purposes until backend integration is complete.
          </Alert>
        )}

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

        {/* Editing Instructions */}
        <Paper sx={{ p: 2, mb: 2, backgroundColor: "info.light" }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: "bold" }}>
              Editing Mode
            </Typography>
            <Button
              variant="contained"
              size="small"
              startIcon={<FiPlus />}
              onClick={handleAddNode}
            >
              Add Task
            </Button>
          </Box>
          <Typography variant="body2">
            • Drag nodes to reposition them
            <br />
            • Connect nodes by dragging from one node's edge to another
            <br />
            • Click on edges to select them, then press Delete/Backspace to remove
            <br />• Click the edit icon on nodes to edit task details
          </Typography>
        </Paper>

        {/* ReactFlow Graph - Editable */}
        <Paper sx={{ height: 600, mb: 3 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            nodesDraggable={true}
            nodesConnectable={true}
            elementsSelectable={true}
            selectNodesOnDrag={false}
            fitView
            attributionPosition="bottom-left"
          >
            <Background />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const task = taskMap.get(node.id)
                return task?.isActive ? "#1976d2" : "#9e9e9e"
              }}
            />
          </ReactFlow>
        </Paper>

        <Button variant="outlined" onClick={() => navigate({ to: "/tasks" })}>
          Back to Objectives
        </Button>

        {/* Task Node Modal */}
        <TaskNodeModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          onSave={handleSaveTask}
          task={selectedTask}
          mode={modalMode}
        />
      </Box>
    </Container>
  )
}

export default EditableObjective
