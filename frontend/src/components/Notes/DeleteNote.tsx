import { Typography } from '@mui/material'
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"

import { ItemsService } from "../../client"
import {
  DialogRoot,
  DialogTitle,
  DialogContent,
  DialogFooter,
} from "../../components/ui/dialog"
import { Button } from "../ui/button"
import useCustomToast from "../../hooks/useCustomToast"

interface DeleteNoteProps {
  id: string
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

const DeleteNote = ({ id, open: controlledOpen, onOpenChange }: DeleteNoteProps) => {
  const [internalOpen, setInternalOpen] = useState(false)
  
  // Use controlled state if provided, otherwise use internal state
  const isOpen = controlledOpen !== undefined ? controlledOpen : internalOpen
  const setIsOpen = onOpenChange || setInternalOpen
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const deleteNote = async (id: string) => {
    await ItemsService.deleteItem({ id: id })
  }

  const mutation = useMutation({
    mutationFn: deleteNote,
    onSuccess: () => {
      showSuccessToast("The note was deleted successfully")
      setIsOpen(false)
    },
    onError: () => {
      showErrorToast("An error occurred while deleting the note")
    },
    onSettled: () => {
      queryClient.invalidateQueries() // Invalidate all queries, assuming no specific queryKey for notes yet
    },
  })

  const onSubmit = async () => {
    mutation.mutate(id)
  }

  return (
    <>
      <DialogRoot
        open={isOpen}
        onOpenChange={(open) => setIsOpen(open)}
        maxWidth="md"
        fullWidth
      >
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>Delete Note</DialogTitle>
          <DialogContent>
            <Typography sx={{ mb: 2 }}>
              This note will be permanently deleted. Are you sure? You will not
              be able to undo this action.
            </Typography>
          </DialogContent>

          <DialogFooter>
            <Button
              variant="outlined"
              onClick={() => setIsOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color="error"
              type="submit"
              loading={isSubmitting}
            >
              Delete
            </Button>
          </DialogFooter>
        </form>
      </DialogRoot>
    </>
  )
}

export default DeleteNote
