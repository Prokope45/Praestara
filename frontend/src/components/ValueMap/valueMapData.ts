import type { Edge, Node } from "reactflow"

const center = { x: 420, y: 320 }
const primaryRadius = 160
const subRadius = 150

const degToRad = (deg: number) => (deg * Math.PI) / 180

export const primarySchemas = [
  { id: "domain_virtue", label: "Virtue", angle: -90 },
  { id: "domain_strategy", label: "Strategy", angle: -135 },
  { id: "domain_execution", label: "Execution", angle: 180 },
  { id: "domain_precision", label: "Precision", angle: 135 },
  { id: "domain_health", label: "Health", angle: 90 },
  { id: "domain_proficiency", label: "Proficiency", angle: 45 },
  { id: "domain_faith", label: "Faith", angle: 0 },
  { id: "domain_philanthropy", label: "Philanthropy", angle: -45 },
]

const primaryPositions = new Map<
  string,
  { x: number; y: number; angle: number }
>()

primarySchemas.forEach((schema) => {
  const rad = degToRad(schema.angle)
  const x = center.x + primaryRadius * Math.cos(rad)
  const y = center.y + primaryRadius * Math.sin(rad)
  primaryPositions.set(schema.id, { x, y, angle: schema.angle })
})

export interface DomainRatingData {
  id?: string
  label: string
  importance: number
  consistency: number
}

// Map known labels to primary schema ids
function mapDomainToSchemaId(label: string): string {
  const lower = label.toLowerCase()
  if (lower.includes("health") || lower.includes("sleep")) return "domain_health"
  if (lower.includes("work")) return "domain_execution"
  if (lower.includes("learning") || lower.includes("skill")) return "domain_proficiency"
  if (lower.includes("relationship") || lower.includes("family") || lower.includes("friend")) return "domain_philanthropy"
  if (lower.includes("community") || lower.includes("service")) return "domain_philanthropy"
  if (lower.includes("spiritual") || lower.includes("existential")) return "domain_faith"
  if (lower.includes("play") || lower.includes("enjoyment")) return "domain_virtue"
  if (lower.includes("order") || lower.includes("responsibility") || lower.includes("maintenance")) return "domain_strategy"
  
  // Fallback if no match
  return "domain_precision"
}

export function generateValueMapData(
  userName: string,
  domainRatings: DomainRatingData[]
): { nodes: Node[]; edges: Edge[] } {
  const spacingDegrees = 36

  const subschema = domainRatings.map((rating, i) => {
    return {
      id: rating.id || `op_${i}`,
      label: rating.label,
      text: `Importance: ${rating.importance}/10 | Consistency: ${rating.consistency}/10`,
      parent: mapDomainToSchemaId(rating.label),
      type: "value_statement",
      importance: rating.importance,
      consistency: rating.consistency,
    }
  })

  const groupedSubschema = subschema.reduce<Record<string, typeof subschema>>(
    (acc, node) => {
      acc[node.parent] = acc[node.parent] ? [...acc[node.parent], node] : [node]
      return acc
    },
    {}
  )

  const nodes: Node[] = [
    {
      id: "user_core",
      type: "user_core",
      position: { x: center.x, y: center.y },
      data: {
        label: userName,
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
        type: node.type,
        position: { x, y },
        data: { 
          label: node.label, 
          text: node.text,
          importance: node.importance,
          consistency: node.consistency
        },
      }
    }),
  ]

  const edges: Edge[] = [
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
  ]

  // Edges connecting schemas to their subschemas
  subschema.forEach((node) => {
    edges.push({
      id: `e_${node.parent}_${node.id}`,
      source: node.parent,
      target: node.id,
      label: "expresses",
    })
  })

  return { nodes, edges }
}

// Provide some default dummy data so we can still render if no real data is passed
export const fallbackValueMapData = generateValueMapData("You", [
  { label: "Health and body care", importance: 8, consistency: 6 },
  { label: "Sleep and recovery", importance: 9, consistency: 7 },
  { label: "Work or contribution", importance: 8, consistency: 8 },
  { label: "Learning or skill building", importance: 7, consistency: 5 },
  { label: "Relationships and friendships", importance: 9, consistency: 8 },
  { label: "Family or close bonds", importance: 10, consistency: 9 },
  { label: "Community or service", importance: 6, consistency: 4 },
  { label: "Spiritual or existential life", importance: 8, consistency: 8 },
  { label: "Play, rest, enjoyment", importance: 7, consistency: 6 },
  { label: "Order, responsibility, life maintenance", importance: 8, consistency: 7 },
])
