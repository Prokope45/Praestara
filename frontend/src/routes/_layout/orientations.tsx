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
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"
import { useState } from "react"

import AddOrientation from "../../components/Orientations/AddOrientation"
import EditableOrientation from "../../components/Orientations/EditableOrientation"
import OrientationDetail from "../../components/Orientations/OrientationDetail"
import OrientationActionsMenu from "../../components/Orientations/OrientationActionsMenu"
import OrientationCard from "../../components/Orientations/OrientationCard"
import PendingItems from "../../components/Pending/PendingItems"
import ViewSwitcher, { ViewMode } from "../../components/Common/ViewSwitcher"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "../../components/ui/pagination"
import { OrientationsService } from "../../client"
import type { OrientationPublic as ApiOrientationPublic } from "../../client"

const orientationsSearchSchema = z.object({
  page: z.number().catch(1),
  orientationId: z.string().optional(),
  editMode: z.string().optional(),
})

const PER_PAGE = 5

function getOrientationsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      OrientationsService.readOrientations({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["orientations", { page }],
  }
}

function getOrientationQueryOptions({ orientationId }: { orientationId: string }) {
  return {
    queryFn: () => OrientationsService.readOrientation({ id: orientationId }),
    queryKey: ["orientations", orientationId],
  }
}

export const Route = createFileRoute("/_layout/orientations")({
  component: Orientations,
  validateSearch: (search) => orientationsSearchSchema.parse(search),
})

interface OrientationsViewProps {
  viewMode: ViewMode
}

function OrientationsView({ viewMode }: OrientationsViewProps) {
  const navigate = useNavigate({ from: Route.fullPath })
  const queryClient = useQueryClient()
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery<{
    data: ApiOrientationPublic[]
    count: number
  }>({
    ...getOrientationsQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) =>
    navigate({
      search: (prev: Record<string, unknown>) => ({ ...prev, page }),
    })

  const handleDelete = () => {
    // Invalidate query to refresh the list
    queryClient.invalidateQueries({ queryKey: ["orientations"] })
  }

  const orientations = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingItems />
  }

  if (orientations.length === 0) {
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
          <Typography variant="h6">You don't have any orientations yet</Typography>
          <Typography variant="body2" color="text.secondary">
            Add a new orientation to start building your self-concept
          </Typography>
        </Stack>
      </Box>
    )
  }

  return (
    <>
      {/* Card View */}
      {viewMode === "card" && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 2,
            mb: 2,
          }}
        >
          {orientations.map((orientation) => (
            <OrientationCard
              key={orientation.id}
              orientation={orientation}
              isPlaceholderData={isPlaceholderData}
              onDelete={handleDelete}
            />
          ))}
        </Box>
      )}

      {/* Table View */}
      {viewMode === "table" && (
        <TableContainer component={Paper} sx={{ mb: 2 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width="35%">Title</TableCell>
                <TableCell width="35%">Description</TableCell>
                <TableCell width="15%">Traits</TableCell>
                <TableCell width="15%">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orientations.map((orientation) => {
                const totalTraits = orientation.traits?.length || 0
                const averageValue =
                  totalTraits > 0
                    ? Math.round(
                        (orientation.traits?.reduce((sum, trait) => sum + trait.value, 0) || 0) /
                          totalTraits
                      )
                    : 0

                return (
                  <TableRow key={orientation.id} sx={{ opacity: isPlaceholderData ? 0.5 : 1 }}>
                    <TableCell
                      sx={{
                        maxWidth: "35%",
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
                              orientationId: orientation.id,
                            }),
                          })
                        }
                      >
                        {orientation.title}
                      </Button>
                    </TableCell>
                    <TableCell
                      sx={{
                        color: !orientation.description ? "text.secondary" : "inherit",
                        maxWidth: "35%",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {orientation.description || "N/A"}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Typography variant="body2">{totalTraits} traits</Typography>
                        {totalTraits > 0 && (
                          <Chip
                            label={`${averageValue}% avg`}
                            size="small"
                            color={averageValue >= 70 ? "success" : "default"}
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <OrientationActionsMenu orientation={orientation} onDelete={handleDelete} />
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Pagination */}
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

function Orientations() {
  const { orientationId, editMode } = Route.useSearch()
  const [viewMode, setViewMode] = useState<ViewMode>("card")

  // Fetch single orientation if orientationId is provided
  const { data: orientation, isLoading: isLoadingOrientation } = useQuery<ApiOrientationPublic>({
    ...getOrientationQueryOptions({ orientationId: orientationId || "" }),
    enabled: !!orientationId,
  })

  if (orientationId) {
    if (isLoadingOrientation) {
      return <PendingItems />
    }

    if (orientation) {
      if (editMode === "true") {
        return <EditableOrientation orientation={orientation} />
      }

      return <OrientationDetail orientation={orientation} />
    }
  }

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6 }}>
        <Typography variant="h4" component="h1">
          Orientations
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
          Define who you want to be and track the traits that make up your aspirations
        </Typography>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 3, mb: 2 }}>
          <AddOrientation />
          <ViewSwitcher defaultView="card" onViewChange={setViewMode} />
        </Box>
        <OrientationsView viewMode={viewMode} />
      </Box>
    </Container>
  )
}

export default Orientations
