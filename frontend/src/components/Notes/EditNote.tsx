import { Box, Stack, TextField, Typography, MenuItem } from '@mui/material'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { Controller } from "react-hook-form"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FaExchangeAlt } from "react-icons/fa"

import { type ApiError, type ItemPublic, ItemsService } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { handleError } from "../../utils"
import {
  DialogRoot,
  DialogTitle,
  DialogContent,
  DialogFooter,
} from "../ui/dialog"
import { Button } from "../ui/button"

interface EditNoteProps {
  note: ItemPublic
}

interface NoteUpdateForm {
  title: string
  description?: string
}

const EditNote = ({ note }: EditNoteProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<NoteUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      ...note,
      description: note.description ?? undefined,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: NoteUpdateForm) =>
      ItemsService.updateItem({ id: note.id, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Note updated successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] })
    },
  })

  const onSubmit: SubmitHandler<NoteUpdateForm> = async (data) => {
    mutation.mutate(data)
  }

  return (
    <>
      <MenuItem onClick={() => setIsOpen(true)}>
        <FaExchangeAlt style={{ marginRight: 8 }} />
        Edit Note
      </MenuItem>

      <DialogRoot
        open={isOpen}
        onOpenChange={(open) => setIsOpen(open)}
        maxWidth="md"
        fullWidth
      >
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>Edit Note</DialogTitle>
          <DialogContent>
            <Typography sx={{ mb: 2 }}>
              Update the note details below.
            </Typography>
            <Stack spacing={3} sx={{ mt: 2 }}>
              <TextField
                id="title"
                label="Title"
                required
                fullWidth
                error={!!errors.title}
                helperText={errors.title?.message}
                {...register("title", {
                  required: "Title is required",
                })}
                placeholder="Title"
              />

              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Body
                </Typography>
                <Box sx={{ height: '300px' }}>
                  <Controller
                    name="description"
                    control={control}
                    render={({ field }) => (
                      <ReactQuill
                        value={field.value || ''}
                        onChange={field.onChange}
                        placeholder="Enter note content here..."
                        style={{ height: '250px', marginBottom: '50px' }}
                        theme="snow"
                      />
                    )}
                  />
                </Box>
              </Box>
            </Stack>
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
              type="submit"
              loading={isSubmitting}
            >
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogRoot>
    </>
  )
}

export default EditNote
