import { Box, Container, Paper, Stack, Typography } from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import ReactFlow, {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  type Node,
  type NodeProps,
  type NodeTypes,
} from "reactflow"
import "reactflow/dist/style.css"

import {
  GoalScaffoldGoalsService,
  GoalScaffoldSelfConceptService,
} from "@/client"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/value-map")({
  component: ValueMap,
})

const baseNodeStyles = {
  borderRadius: 12,
  padding: "8px 10px",
  width: "fit-content",
  maxWidth: 200,
  display: "inline-flex",
  flexDirection: "column",
  gap: 1,
  boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
}

const typeStyles: Record<string, React.CSSProperties> = {
  user_core: {
    background: "linear-gradient(135deg, #111827 0%, #4338ca 100%)",
    color: "#f8fafc",
    border: "1px solid rgba(255,255,255,0.2)",
    width: 170,
    height: 150,
    clipPath: "polygon(25% 6%, 75% 6%, 100% 50%, 75% 94%, 25% 94%, 0% 50%)",
    justifyContent: "center",
    alignItems: "center",
    textAlign: "center",
    padding: "18px 14px",
  },
  value_domain: {
    background: "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
    border: "1px solid #f59e0b",
  },
  goal_direction: {
    background: "linear-gradient(135deg, #dcfce7 0%, #86efac 100%)",
    border: "1px solid #22c55e",
  },
}

const ValueNode = ({ data, type }: NodeProps) => {
  return (
    <Box sx={{ ...baseNodeStyles, ...typeStyles[type ?? "value_domain"] }}>
      <Typography
        variant="subtitle2"
        sx={{ fontWeight: 700, color: type === "user_core" ? "inherit" : "text.primary" }}
      >
        {data.label}
      </Typography>
      {data.text ? (
        <Typography
          variant="caption"
          sx={{ color: type === "user_core" ? "rgba(248,250,252,0.8)" : "text.secondary" }}
        >
          {data.text}
        </Typography>
      ) : null}
    </Box>
  )
}

const UserCoreNode = ({ data }: NodeProps) => {
  return (
    <Box sx={{ ...baseNodeStyles, ...typeStyles.user_core, position: "relative" }}>
      <Handle id="top" type="source" position={Position.Top} style={{ top: 8, left: "50%" }} />
      <Handle id="right" type="source" position={Position.Right} style={{ right: 6, top: "50%" }} />
      <Handle id="bottom" type="source" position={Position.Bottom} style={{ bottom: 8, left: "50%" }} />
      <Handle id="left" type="source" position={Position.Left} style={{ left: 6, top: "50%" }} />
      <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: data.text ? 0.5 : 0 }}>
        {data.label}
      </Typography>
      {data.text ? (
        <Typography variant="caption" sx={{ color: "rgba(248,250,252,0.8)" }}>
          {data.text}
        </Typography>
      ) : null}
    </Box>
  )
}

const nodeTypes: NodeTypes = {
  user_core: UserCoreNode,
  value_domain: ValueNode,
  goal_direction: ValueNode,
}

function ValueMap() {
  const { user } = useAuth()
  const { data: latestSnapshot } = useQuery({
    queryKey: ["self-concept", "snapshot"],
    queryFn: () => GoalScaffoldSelfConceptService.goalScaffoldGetLatestSnapshot(),
  })
  const { data: goalsData } = useQuery({
    queryKey: ["goal-scaffold", "goals"],
    queryFn: () => GoalScaffoldGoalsService.goalScaffoldListGoals({ limit: 20, skip: 0 }),
  })

  const dimensions = (latestSnapshot?.dimensions ?? {}) as Record<string, number>
  const dimensionEntries = Object.entries(dimensions)
  const goals = goalsData?.data ?? []

  const nodes: Node[] =
    dimensionEntries.length === 0 && goals.length === 0
      ? []
      : [
          {
            id: "user_core",
            type: "user_core",
            position: { x: 420, y: 320 },
            data: {
              label: user?.full_name || user?.email || "You",
              text: "Live deterministic state",
            },
          },
          ...dimensionEntries.map(([name, value], index) => {
            const angle = (-90 + index * (360 / Math.max(dimensionEntries.length, 1))) * (Math.PI / 180)
            return {
              id: `dim_${name}`,
              type: "value_domain",
              position: {
                x: 420 + 220 * Math.cos(angle),
                y: 320 + 220 * Math.sin(angle),
              },
              data: {
                label: name.split("_").join(" "),
                text: `${Math.round(Number(value) * 100)} / 100`,
              },
            }
          }),
          ...goals.map((goal, index) => {
            const angle = (-80 + index * (320 / Math.max(goals.length, 1))) * (Math.PI / 180)
            return {
              id: `goal_${goal.id}`,
              type: "goal_direction",
              position: {
                x: 420 + 390 * Math.cos(angle),
                y: 320 + 390 * Math.sin(angle),
              },
              data: {
                label: goal.title,
                text: `${goal.target_value} ${goal.target_unit}`,
              },
            }
          }),
        ]

  const edges =
    dimensionEntries.length === 0 && goals.length === 0
      ? []
      : [
          ...dimensionEntries.map(([name], index) => {
            const handles = ["top", "right", "bottom", "left"]
            return {
              id: `edge_dim_${name}`,
              source: "user_core",
              sourceHandle: handles[index % handles.length],
              target: `dim_${name}`,
              label: "tracks",
            }
          }),
          ...goals.map((goal) => {
            const sourceKey =
              goal.category === "exercise"
                ? "self_efficacy"
                : goal.category === "sleep"
                  ? "well_being"
                  : goal.category === "nutrition"
                    ? "goal_clarity"
                    : "motivation"
            return {
              id: `edge_goal_${goal.id}`,
              source: dimensions[sourceKey] !== undefined ? `dim_${sourceKey}` : "user_core",
              target: `goal_${goal.id}`,
              label: "expresses",
            }
          }),
        ]

  return (
    <Container maxWidth={false}>
      <Stack spacing={3} sx={{ pt: 6 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Value Map
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Connected self-concept dimensions and current weekly goals.
          </Typography>
        </Box>

        <Paper sx={{ height: 700, position: "relative", overflow: "hidden" }}>
          {nodes.length === 0 ? (
            <Box sx={{ p: 4 }}>
              <Typography color="text.secondary">
                Complete onboarding first. This map will populate from your self-concept baseline and weekly goals.
              </Typography>
            </Box>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              nodeOrigin={[0.5, 0.5]}
              fitView
              defaultEdgeOptions={{
                markerEnd: { type: MarkerType.ArrowClosed, color: "#7c3aed" },
                style: { stroke: "#7c3aed", strokeWidth: 2 },
                labelStyle: { fill: "#6b7280", fontSize: 10 },
              }}
            >
              <Background color="#e2e8f0" gap={18} />
              <Controls />
            </ReactFlow>
          )}
        </Paper>
      </Stack>
    </Container>
  )
}
