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
} from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"

import AddWorkflow from "../../components/Workflows/AddWorkflow"
import DeleteWorkflow from "../../components/Workflows/DeleteWorkflow"
import EditableWorkflow from "../../components/Workflows/EditableWorkflow"
import EditWorkflow from "../../components/Workflows/EditWorkflow"
import WorkflowDetail from "../../components/Workflows/WorkflowDetail"
import PendingItems from "../../components/Pending/PendingItems"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "../../components/ui/pagination"

// Placeholder type for workflow - will be replaced with actual backend type
interface WorkflowPublic {
  id: string
  title: string
  description?: string
}

const tasksSearchSchema = z.object({
  page: z.number().catch(1),
  workflowId: z.string().optional(),
  editMode: z.string().optional(),
})

const PER_PAGE = 5

function getWorkflowsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () => {
      // Placeholder data until backend is implemented
      const mockWorkflows: WorkflowPublic[] = [
        { id: "1", title: "Project Setup", description: "Initial project setup workflow" },
        { id: "2", title: "Development Process", description: "Software development workflow" },
        { id: "3", title: "Testing Pipeline", description: "QA and testing workflow" },
        { id: "4", title: "Deployment", description: "Production deployment workflow" },
        { id: "5", title: "Monitoring", description: "System monitoring workflow" },
      ]
      return Promise.resolve({
        data: mockWorkflows,
        count: mockWorkflows.length,
      })
    },
    queryKey: ["workflows", { page }],
  }
}

export const Route = createFileRoute("/_layout/tasks")({
  component: Tasks,
  validateSearch: (search) => tasksSearchSchema.parse(search),
})

function WorkflowsTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getWorkflowsQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) =>
    navigate({
      search: (prev: Record<string, unknown>) => ({ ...prev, page }),
    })

  const workflows = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingItems />
  }

  if (workflows.length === 0) {
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
          <Typography variant="h6">You don't have any workflows yet</Typography>
          <Typography variant="body2" color="text.secondary">
            Add a new workflow to get started
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
              <TableCell width="20%">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {workflows?.map((workflow) => (
              <TableRow 
                key={workflow.id} 
                sx={{ opacity: isPlaceholderData ? 0.5 : 1 }}
              >
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
                    onClick={() => navigate({
                      search: (prev: Record<string, unknown>) => ({ ...prev, workflowId: workflow.id })
                    })}
                  >
                    {workflow.title}
                  </Button>
                </TableCell>
                <TableCell
                  sx={{
                    color: !workflow.description ? "text.secondary" : "inherit",
                    maxWidth: "40%",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {workflow.description || "N/A"}
                </TableCell>
                <TableCell width="20%">
                  <Box display="flex" gap={1}>
                    <EditWorkflow workflow={workflow} />
                    <DeleteWorkflow workflow={workflow} />
                  </Box>
                </TableCell>
              </TableRow>
            ))}
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
  const { workflowId, editMode } = Route.useSearch()

  if (workflowId) {
    // Find the workflow by ID (in a real app, this would be a separate query)
    const mockWorkflows: WorkflowPublic[] = [
      { id: "1", title: "Project Setup", description: "Initial project setup workflow" },
      { id: "2", title: "Development Process", description: "Software development workflow" },
      { id: "3", title: "Testing Pipeline", description: "QA and testing workflow" },
      { id: "4", title: "Deployment", description: "Production deployment workflow" },
      { id: "5", title: "Monitoring", description: "System monitoring workflow" },
    ]

    const workflow = mockWorkflows.find(w => w.id === workflowId)

    if (workflow) {
      if (editMode === "true") {
        return (
          <Container maxWidth={false}>
            <EditableWorkflow workflow={workflow} />
          </Container>
        )
      }

      return (
        <Container maxWidth={false}>
          <WorkflowDetail workflow={workflow} />
        </Container>
      )
    }
  }

  return (
    <Container maxWidth={false}>
      <Typography variant="h4" component="h1" sx={{ pt: 6 }}>
        Workflows Management
      </Typography>
      <AddWorkflow />
      <WorkflowsTable />
    </Container>
  )
}

export default Tasks
