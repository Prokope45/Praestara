import { useState } from "react"
import { useNavigate } from "@tanstack/react-router"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import type { ItemPublic } from "../../client"
import { ItemsService } from "../../client"
import type { ApiError } from "../../client/core/ApiError"
import useCustomToast from "../../hooks/useCustomToast"
import { handleError } from "../../utils"
import { ActionsMenu } from "../Common/ActionsMenu"
import DeleteNote from "./DeleteNote"

interface ItemActionsMenuProps {
  note: ItemPublic
}

export const ItemActionsMenu = ({ note }: ItemActionsMenuProps) => {
  const navigate = useNavigate()
  const [deleteOpen, setDeleteOpen] = useState(false)
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
    <>
      <ActionsMenu
        onView={handleView}
        onEdit={handleEdit}
        onDelete={handleDelete}
        isDeleting={deleteMutation.isPending}
        showView={true}
      />

      <DeleteNote id={note.id} open={deleteOpen} onOpenChange={setDeleteOpen} />
    </>
  )
}
