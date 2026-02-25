import type { Edge, Node } from "reactflow"

const center = { x: 420, y: 320 }
const primaryRadius = 160
const subRadius = 150

const degToRad = (deg: number) => (deg * Math.PI) / 180

const primarySchemas = [
  { id: "domain_virtue", label: "Virtue", angle: -90 },
  { id: "domain_strategy", label: "Strategy", angle: -135 },
  { id: "domain_execution", label: "Execution", angle: 180 },
  { id: "domain_precision", label: "Precision", angle: 135 },
  { id: "domain_health", label: "Health", angle: 90 },
  { id: "domain_proficiency", label: "Proficiency", angle: 45 },
  { id: "domain_faith", label: "Faith", angle: 0 },
  { id: "domain_philanthropy", label: "Philanthropy", angle: -45 },
]

const subschema = [
  {
    id: "op_integrity",
    label: "Integrity",
    text: "Hold the standard even under pressure.",
    parent: "domain_virtue",
  },
  {
    id: "op_organization",
    label: "Organization",
    text: "Order, planning, and structure.",
    parent: "domain_strategy",
  },
  {
    id: "op_deliberate",
    label: "Deliberate action",
    text: "Act with intention, not impulse.",
    parent: "domain_execution",
  },
  {
    id: "op_creativity",
    label: "Creativity + conscientiousness",
    text: "Invent with care and integrity.",
    parent: "domain_precision",
  },
  {
    id: "op_nutrition",
    label: "Nutrition",
    text: "",
    parent: "domain_health",
    type: "goal_direction",
  },
  {
    id: "op_fitness",
    label: "Fitness",
    text: "",
    parent: "domain_health",
    type: "goal_direction",
  },
  {
    id: "op_skill",
    label: "Skill refinement",
    text: "Deliberate practice and feedback loops.",
    parent: "domain_proficiency",
  },
  {
    id: "op_prayer",
    label: "Prayer + solitude",
    text: "Reflection, silence, and inner alignment.",
    parent: "domain_faith",
  },
  {
    id: "op_social",
    label: "Social connection",
    text: "Build bonds with care and presence.",
    parent: "domain_philanthropy",
  },
  {
    id: "op_community",
    label: "Community + charity",
    text: "Serve beyond the self.",
    parent: "domain_philanthropy",
  },
]

const primaryPositions = new Map<string, { x: number; y: number; angle: number }>()

primarySchemas.forEach((schema) => {
  const rad = degToRad(schema.angle)
  const x = center.x + primaryRadius * Math.cos(rad)
  const y = center.y + primaryRadius * Math.sin(rad)
  primaryPositions.set(schema.id, { x, y, angle: schema.angle })
})

const groupedSubschema = subschema.reduce<Record<string, typeof subschema>>((acc, node) => {
  acc[node.parent] = acc[node.parent] ? [...acc[node.parent], node] : [node]
  return acc
}, {})

const spacingDegrees = 36

export const demoValueMapNodes: Node[] = [
  {
    id: "user_core",
    type: "user_core",
    position: { x: center.x, y: center.y },
    data: {
      label: "Ethan",
      text: "Central identity",
    },
  },
  ...primarySchemas.map((schema) => {
    const pos = primaryPositions.get(schema.id)
    return {
      id: schema.id,
      type: "value_domain",
      position: { x: pos?.x ?? 0, y: pos?.y ?? 0 },
      data: { label: schema.label },
    }
  }),
  ...subschema.map((node) => {
    const parent = primaryPositions.get(node.parent)
    const siblings = groupedSubschema[node.parent] ?? []
    const index = siblings.findIndex((item) => item.id === node.id)
    const count = siblings.length || 1
    const offset = (index - (count - 1) / 2) * spacingDegrees
    const angle = (parent?.angle ?? 0) + offset
    const rad = degToRad(angle)
    const x = (parent?.x ?? center.x) + subRadius * Math.cos(rad)
    const y = (parent?.y ?? center.y) + subRadius * Math.sin(rad)
    return {
      id: node.id,
      type: node.type ?? "value_statement",
      position: { x, y },
      data: { label: node.label, text: node.text },
    }
  }),
]

export const demoValueMapEdges: Edge[] = [
  { id: "e_user_virtue", source: "user_core", sourceHandle: "top", target: "domain_virtue", label: "anchors" },
  { id: "e_user_strategy", source: "user_core", sourceHandle: "topLeft", target: "domain_strategy", label: "anchors" },
  { id: "e_user_execution", source: "user_core", sourceHandle: "left", target: "domain_execution", label: "anchors" },
  { id: "e_user_precision", source: "user_core", sourceHandle: "bottomLeft", target: "domain_precision", label: "anchors" },
  { id: "e_user_health", source: "user_core", sourceHandle: "bottom", target: "domain_health", label: "anchors" },
  { id: "e_user_proficiency", source: "user_core", sourceHandle: "bottomRight", target: "domain_proficiency", label: "anchors" },
  { id: "e_user_faith", source: "user_core", sourceHandle: "right", target: "domain_faith", label: "anchors" },
  { id: "e_user_philanthropy", source: "user_core", sourceHandle: "topRight", target: "domain_philanthropy", label: "anchors" },
  { id: "e_virtue_strategy", source: "domain_virtue", target: "domain_strategy", label: "guides" },
  { id: "e_virtue_execution", source: "domain_virtue", target: "domain_execution", label: "guides" },
  { id: "e_virtue_precision", source: "domain_virtue", target: "domain_precision", label: "guides" },
  { id: "e_virtue_health", source: "domain_virtue", target: "domain_health", label: "guides" },
  { id: "e_virtue_proficiency", source: "domain_virtue", target: "domain_proficiency", label: "guides" },
  { id: "e_virtue_faith", source: "domain_virtue", target: "domain_faith", label: "guides" },
  { id: "e_virtue_philanthropy", source: "domain_virtue", target: "domain_philanthropy", label: "guides" },
  { id: "e_strategy_org", source: "domain_strategy", target: "op_organization", label: "operationalizes" },
  { id: "e_execution_deliberate", source: "domain_execution", target: "op_deliberate", label: "operationalizes" },
  { id: "e_precision_creativity", source: "domain_precision", target: "op_creativity", label: "operationalizes" },
  { id: "e_health_nutrition", source: "domain_health", target: "op_nutrition", label: "supports" },
  { id: "e_health_fitness", source: "domain_health", target: "op_fitness", label: "supports" },
  { id: "e_philanthropy_community", source: "domain_philanthropy", target: "op_community", label: "expresses" },
  { id: "e_faith_prayer", source: "domain_faith", target: "op_prayer", label: "expresses" },
  { id: "e_virtue_integrity", source: "domain_virtue", target: "op_integrity", label: "expresses" },
  { id: "e_proficiency_skill", source: "domain_proficiency", target: "op_skill", label: "expresses" },
  { id: "e_philanthropy_social", source: "domain_philanthropy", target: "op_social", label: "expresses" },
]
