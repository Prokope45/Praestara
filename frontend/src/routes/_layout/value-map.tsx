import { Box, Container, Paper, Stack, Typography } from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import ReactFlow, {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  type NodeProps,
  type NodeTypes,
} from "reactflow"
import "reactflow/dist/style.css"

import { demoValueMapEdges, demoValueMapNodes } from "@/components/ValueMap/valueMapData"

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
  core_identity: {
    background: "linear-gradient(135deg, #ede9fe 0%, #c4b5fd 100%)",
    border: "1px solid #a78bfa",
  },
  value_domain: {
    background: "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
    border: "1px solid #f59e0b",
  },
  value_statement: {
    background: "linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)",
    border: "1px solid #60a5fa",
  },
  goal_direction: {
    background: "linear-gradient(135deg, #dcfce7 0%, #86efac 100%)",
    border: "1px solid #22c55e",
  },
  friction: {
    background: "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)",
    border: "1px solid #ef4444",
  },
}

const ValueNode = ({ data, type }: NodeProps) => {
  return (
    <Box sx={{ ...baseNodeStyles, ...typeStyles[type ?? "value_domain"] }}>
      <Typography
        variant="subtitle2"
        sx={{
          fontWeight: 700,
          mb: 0,
          color: type === "user_core" ? "inherit" : "text.primary",
        }}
      >
        {data.label}
      </Typography>
      {data.text && (
        <Typography
          variant="caption"
          sx={{ color: type === "user_core" ? "rgba(248,250,252,0.8)" : "text.secondary" }}
        >
          {data.text}
        </Typography>
      )}
    </Box>
  )
}

const UserCoreNode = ({ data }: NodeProps) => {
  return (
    <Box sx={{ ...baseNodeStyles, ...typeStyles.user_core, position: "relative" }}>
      <Handle id="top" type="source" position={Position.Top} style={{ top: 8, left: "50%" }} />
      <Handle
        id="topRight"
        type="source"
        position={Position.Top}
        style={{ top: 18, left: "82%" }}
      />
      <Handle
        id="right"
        type="source"
        position={Position.Right}
        style={{ right: 6, top: "50%" }}
      />
      <Handle
        id="bottomRight"
        type="source"
        position={Position.Bottom}
        style={{ bottom: 14, left: "82%" }}
      />
      <Handle
        id="bottom"
        type="source"
        position={Position.Bottom}
        style={{ bottom: 8, left: "50%" }}
      />
      <Handle
        id="bottomLeft"
        type="source"
        position={Position.Bottom}
        style={{ bottom: 14, left: "18%" }}
      />
      <Handle
        id="left"
        type="source"
        position={Position.Left}
        style={{ left: 6, top: "50%" }}
      />
      <Handle
        id="topLeft"
        type="source"
        position={Position.Top}
        style={{ top: 18, left: "18%" }}
      />
      <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: data.text ? 0.5 : 0 }}>
        {data.label}
      </Typography>
      {data.text && (
        <Typography variant="caption" sx={{ color: "rgba(248,250,252,0.8)" }}>
          {data.text}
        </Typography>
      )}
    </Box>
  )
}

const nodeTypes: NodeTypes = {
  user_core: UserCoreNode,
  core_identity: ValueNode,
  value_domain: ValueNode,
  value_statement: ValueNode,
  goal_direction: ValueNode,
  friction: ValueNode,
}

function ValueMap() {
  return (
    <Container maxWidth={false}>
      <Stack spacing={3} sx={{ pt: 6 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Value Map
          </Typography>
          <Typography variant="body1" color="text.secondary">
            A living map of values, identity, and directional goals.
          </Typography>
        </Box>

        <Paper sx={{ height: 700, position: "relative", overflow: "hidden" }}>
          <ReactFlow
            nodes={demoValueMapNodes}
            edges={demoValueMapEdges}
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
        </Paper>
      </Stack>
    </Container>
  )
}
