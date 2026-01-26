import { Card, CardContent, CardActions, Typography } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import type { ItemPublic } from "../../client"
import { ActionsMenu } from "../Common/ActionsMenu"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ItemsService } from "../../client"
import type { ApiError } from "../../client/core/ApiError"
import useCustomToast from "../../hooks/useCustomToast"
import { handleError } from "../../utils"

interface NoteCardProps {
  note: ItemPublic
  isPlaceholderData?: boolean
}

const NoteCard = ({ note, isPlaceholderData = false }: NoteCardProps) => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: (id: string) => ItemsService.deleteItem({ id }),
    onSuccess: () => {
      showSuccessToast("Note deleted successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] })
    },
  })

  // Strip HTML tags and truncate to 100 characters
  const stripHtml = (html: string) => {
    const tmp = document.createElement("DIV")
    tmp.innerHTML = html
    // Get text content and normalize whitespace
    const text = tmp.textContent || tmp.innerText || ""
    // Replace multiple spaces/newlines with single space and trim
    return text.replace(/\s+/g, ' ').trim()
  }

  const plainText = note.description ? stripHtml(note.description) : "No description"
  const truncatedText = plainText.length > 100 
    ? plainText.substring(0, 100) + "..." 
    : plainText

  const handleView = () => {
    navigate({
      to: "/notes",
      search: (prev: Record<string, unknown>) => ({ ...prev, noteId: note.id }),
    })
  }

  const handleEdit = () => {
    navigate({
      to: "/notes",
      search: (prev: Record<string, unknown>) => ({ ...prev, noteId: note.id, editMode: "true" }),
    })
  }

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete "${note.title}"?`)) {
      deleteMutation.mutate(note.id)
    }
  }

  return (
    <Card
      sx={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        opacity: isPlaceholderData ? 0.5 : 1,
        transition: "transform 0.2s, box-shadow 0.2s",
        cursor: "pointer",
        "&:hover": {
          transform: "translateY(-2px)",
          boxShadow: 4,
        },
      }}
    >
      <CardContent 
        sx={{ flexGrow: 1 }}
        onClick={handleView}
      >
        <Typography variant="h6" sx={{ fontWeight: "bold", mb: 1 }}>
          {note.title}
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
        >
          {truncatedText}
        </Typography>
      </CardContent>
      <CardActions 
        sx={{ justifyContent: "flex-end", pt: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <ActionsMenu
          onView={handleView}
          onEdit={handleEdit}
          onDelete={handleDelete}
          isDeleting={deleteMutation.isPending}
          showView={true}
        />
      </CardActions>
    </Card>
  )
}

export default NoteCard
