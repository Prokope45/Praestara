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
  Card,
  CardContent,
  CardActions,
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
import PendingItems from "../../components/Pending/PendingItems"
import ViewSwitcher, { ViewMode } from "../../components/Common/ViewSwitcher"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "../../components/ui/pagination"
import { sampleOrientations } from "../../data/sampleOrientations"
import { getTempOrientations } from "../../utils/tempOrientationStorage"

const orientationsSearchSchema = z.object({
  page: z.number().catch(1),
  orientationId: z.string().optional(),
  editMode: z.string().optional(),
})

const PER_PAGE = 5

function getOrientationsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () => {
      // Merge sample orientations with temp orientations from localStorage
      const tempOrientations = getTempOrientations()
      const allOrientations = [...tempOrientations, ...sampleOrientations]

      return Promise.resolve({
        data: allOrientations,
        count: allOrientations.length,
      })
    },
    queryKey: ["orientations", { page }],
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

  const { data, isLoading, isPlaceholderData } = useQuery({
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
          {orientations.map((orientation) => {
            const totalTraits = orientation.traits.length
            const averageValue =
              totalTraits > 0
                ? Math.round(
                    orientation.traits.reduce((sum, trait) => sum + trait.value, 0) /
                      totalTraits
                  )
                : 0

            return (
              <Card
                key={orientation.id}
                sx={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  opacity: isPlaceholderData ? 0.5 : 1,
                  transition: "transform 0.2s, box-shadow 0.2s",
                  cursor: "pointer",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: 4,
                  },
                }}
                onClick={() =>
                  navigate({
                    search: (prev: Record<string, unknown>) => ({
                      ...prev,
                      orientationId: orientation.id,
                    }),
                  })
                }
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: "bold", mb: 1 }}>
                    {orientation.title}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      mb: 2,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                    }}
                  >
                    {orientation.description || "No description"}
                  </Typography>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
                    <Chip label={`${totalTraits} traits`} size="small" variant="outlined" />
                    {totalTraits > 0 && (
                      <Chip
                        label={`${averageValue}% avg`}
                        size="small"
                        color={averageValue >= 70 ? "success" : "default"}
                      />
                    )}
                  </Box>
                </CardContent>
                <CardActions
                  sx={{ justifyContent: "flex-end", pt: 0 }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <OrientationActionsMenu orientation={orientation} onDelete={handleDelete} />
                </CardActions>
              </Card>
            )
          })}
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
                const totalTraits = orientation.traits.length
                const averageValue =
                  totalTraits > 0
                    ? Math.round(
                        orientation.traits.reduce((sum, trait) => sum + trait.value, 0) /
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

  if (orientationId) {
    // Find the orientation by ID - check temp orientations first, then sample orientations
    const tempOrientations = getTempOrientations()
    const allOrientations = [...tempOrientations, ...sampleOrientations]
    const orientation = allOrientations.find((o) => o.id === orientationId)

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
