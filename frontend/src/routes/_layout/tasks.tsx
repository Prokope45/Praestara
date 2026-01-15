import {
  Button,
  Container,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Stack,
  Chip,
} from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"

import AddObjective from "../../components/Objectives/AddObjective"
import EditableObjective from "../../components/Objectives/EditableObjective"
import ObjectiveDetail from "../../components/Objectives/ObjectiveDetail"
import ObjectiveActionsMenu from "../../components/Objectives/ObjectiveActionsMenu"
import PendingItems from "../../components/Pending/PendingItems"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "../../components/ui/pagination"
import { sampleObjectives } from "../../data/sampleObjectives"
import { getTempObjectives } from "../../utils/tempObjectiveStorage"

const tasksSearchSchema = z.object({
  page: z.number().catch(1),
  objectiveId: z.string().optional(),
  editMode: z.string().optional(),
})

const PER_PAGE = 5

function getObjectivesQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () => {
      // Merge sample objectives with temp objectives from localStorage
      const tempObjectives = getTempObjectives()
      const allObjectives = [...tempObjectives, ...sampleObjectives]
      
      return Promise.resolve({
        data: allObjectives,
        count: allObjectives.length,
      })
    },
    queryKey: ["objectives", { page }],
  }
}

export const Route = createFileRoute("/_layout/tasks")({
  component: Tasks,
  validateSearch: (search) => tasksSearchSchema.parse(search),
})

function ObjectivesTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getObjectivesQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) =>
    navigate({
      search: (prev: Record<string, unknown>) => ({ ...prev, page }),
    })

  const objectives = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingItems />
  }

  if (objectives.length === 0) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          py: 8,
          textAlign: "center",
        }}
      >
        <FiSearch size={48} style={{ marginBottom: 16, opacity: 0.5 }} />
        <Stack spacing={1}>
          <Typography variant="h6">You don't have any objectives yet</Typography>
          <Typography variant="body2" color="text.secondary">
            Add a new objective to get started
          </Typography>
        </Stack>
      </Box>
    )
  }

  return (
    <>
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell width="30%">Title</TableCell>
              <TableCell width="40%">Description</TableCell>
              <TableCell width="15%">Progress</TableCell>
              <TableCell width="15%">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {objectives?.map((objective) => {
              const completedTasks = objective.tasks.filter((t) => !t.isActive).length
              const totalTasks = objective.tasks.length
              const percentComplete = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

              return (
                <TableRow key={objective.id} sx={{ opacity: isPlaceholderData ? 0.5 : 1 }}>
                  <TableCell
                    sx={{
                      maxWidth: "30%",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    <Button
                      variant="text"
                      onClick={() =>
                        navigate({
                          search: (prev: Record<string, unknown>) => ({
                            ...prev,
                            objectiveId: objective.id,
                          }),
                        })
                      }
                    >
                      {objective.title}
                    </Button>
                  </TableCell>
                  <TableCell
                    sx={{
                      color: !objective.description ? "text.secondary" : "inherit",
                      maxWidth: "40%",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {objective.description || "N/A"}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Typography variant="body2">
                        {completedTasks}/{totalTasks}
                      </Typography>
                      <Chip
                        label={`${percentComplete}%`}
                        size="small"
                        color={percentComplete === 100 ? "success" : "default"}
                      />
                    </Box>
                  </TableCell>
                  <TableCell>
                    <ObjectiveActionsMenu objective={objective} />
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
      <Box display="flex" justifyContent="flex-end" mt={2}>
        <PaginationRoot
          count={count}
          pageSize={PER_PAGE}
          page={page}
          onPageChange={({ page }) => setPage(page)}
        >
          <Box display="flex" gap={1}>
            <PaginationPrevTrigger />
            <PaginationItems />
            <PaginationNextTrigger />
          </Box>
        </PaginationRoot>
      </Box>
    </>
  )
}

function Tasks() {
  const { objectiveId, editMode } = Route.useSearch()

  if (objectiveId) {
    // Find the objective by ID - check temp objectives first, then sample objectives
    const tempObjectives = getTempObjectives()
    const allObjectives = [...tempObjectives, ...sampleObjectives]
    const objective = allObjectives.find((o) => o.id === objectiveId)

    if (objective) {
      if (editMode === "true") {
        return <EditableObjective objective={objective} />
      }

      return <ObjectiveDetail objective={objective} />
    }
  }

  return (
    <Container maxWidth={false}>
      <Typography variant="h4" component="h1" sx={{ pt: 6 }}>
        Objectives Management
      </Typography>
      <AddObjective />
      <ObjectivesTable />
    </Container>
  )
}

export default Tasks
