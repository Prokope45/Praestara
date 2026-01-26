import {
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
import { useState } from "react"

import { ItemsService } from "../../client"
import type { ItemPublic } from "../../client"
import { ItemActionsMenu } from "../../components/Common/NoteActionsMenu"
import AddNote from "../../components/Notes/AddNote"
import NoteCard from "../../components/Notes/NoteCard"
import NoteDetail from "../../components/Notes/NoteDetail"
import EditableNote from "../../components/Notes/EditableNote"
import PendingItems from "../../components/Pending/PendingItems"
import ViewSwitcher, { ViewMode } from "../../components/Common/ViewSwitcher"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "../../components/ui/pagination"

const notesSearchSchema = z.object({
  page: z.number().catch(1),
  noteId: z.string().optional(),
  editMode: z.string().optional(),
})

const PER_PAGE = 5

function getNotesQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      ItemsService.readItems({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["notes", { page }],
  }
}

function getNoteQueryOptions({ noteId }: { noteId: string }) {
  return {
    queryFn: () => ItemsService.readItem({ id: noteId }),
    queryKey: ["note", noteId],
  }
}

export const Route = createFileRoute("/_layout/notes")({
  component: Notes,
  validateSearch: (search) => notesSearchSchema.parse(search),
})

interface NotesViewProps {
  viewMode: ViewMode
}

function NotesView({ viewMode }: NotesViewProps) {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getNotesQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) =>
    navigate({
      search: (prev: Record<string, unknown>) => ({ ...prev, page }),
    })

  const notes = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingItems />
  }

  if (notes.length === 0) {
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
          <Typography variant="h6">You don't have any notes yet</Typography>
          <Typography variant="body2" color="text.secondary">
            Add a new note to get started
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
            display: "flex",
            flexDirection: "column",
            gap: 2,
            mb: 2,
          }}
        >
          {notes.map((note) => (
            <NoteCard key={note.id} note={note} isPlaceholderData={isPlaceholderData} />
          ))}
        </Box>
      )}

      {/* Table View */}
      {viewMode === "table" && (
        <TableContainer component={Paper} sx={{ mb: 2 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width="30%">Title</TableCell>
                <TableCell width="30%">Description</TableCell>
                <TableCell width="10%">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {notes.map((note) => (
                <TableRow key={note.id} sx={{ opacity: isPlaceholderData ? 0.5 : 1 }}>
                  <TableCell
                    sx={{
                      maxWidth: "30%",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {note.title}
                  </TableCell>
                  <TableCell
                    sx={{
                      color: !note.description ? "text.secondary" : "inherit",
                      maxWidth: "30%",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {note.description || "N/A"}
                  </TableCell>
                  <TableCell width="10%">
                    <ItemActionsMenu note={note} />
                  </TableCell>
                </TableRow>
              ))}
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

function Notes() {
  const { noteId, editMode } = Route.useSearch()
  const [viewMode, setViewMode] = useState<ViewMode>("card")

  // Fetch single note if noteId is provided
  const { data: note, isLoading: isLoadingNote } = useQuery<ItemPublic>({
    ...getNoteQueryOptions({ noteId: noteId || "" }),
    enabled: !!noteId,
  })

  if (noteId) {
    if (isLoadingNote) {
      return <PendingItems />
    }

    if (note) {
      if (editMode === "true") {
        return <EditableNote note={note} />
      }

      return <NoteDetail note={note} />
    }
  }

  return (
    <Container maxWidth={false}>
      <Typography variant="h4" component="h1" sx={{ pt: 6 }}>
        Notes Management
      </Typography>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 3, mb: 2 }}>
        <AddNote />
        <ViewSwitcher defaultView="card" onViewChange={setViewMode} />
      </Box>
      <NotesView viewMode={viewMode} />
    </Container>
  )
}
