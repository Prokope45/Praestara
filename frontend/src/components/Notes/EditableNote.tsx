import { Container, Typography, Box, Button, Paper, Stack, TextField } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import { useCallback } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { FiSave } from "react-icons/fi"
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import type { ItemPublic, ApiError } from "../../client"
import { ItemsService } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { handleError } from "../../utils"

interface EditableNoteProps {
  note: ItemPublic
}

interface NoteUpdateForm {
  title: string
  description?: string
}

const EditableNote = ({ note }: EditableNoteProps) => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<NoteUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      title: note.title,
      description: note.description ?? undefined,
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: NoteUpdateForm) =>
      ItemsService.updateItem({ id: note.id, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Note updated successfully.")
      // Navigate back to view mode
      navigate({
        to: "/notes",
        search: (prev: Record<string, unknown>) => ({ ...prev, noteId: note.id, editMode: undefined }),
      })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] })
      queryClient.invalidateQueries({ queryKey: ["note", note.id] })
    },
  })

  const handleCancel = useCallback(() => {
    navigate({
      to: "/notes",
      search: (prev: Record<string, unknown>) => ({ ...prev, noteId: note.id, editMode: undefined }),
    })
  }, [navigate, note.id])

  const onSubmit: SubmitHandler<NoteUpdateForm> = useCallback((data) => {
    updateMutation.mutate(data)
  }, [updateMutation])

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h4" component="h1">
            Edit Note
          </Typography>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button variant="outlined" onClick={handleCancel} disabled={updateMutation.isPending}>
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={<FiSave />}
              onClick={handleSubmit(onSubmit)}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </Box>
        </Box>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Stack spacing={3}>
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
              <Box sx={{ height: '400px' }}>
                <Controller
                  name="description"
                  control={control}
                  render={({ field }) => (
                    <ReactQuill
                      value={field.value || ''}
                      onChange={field.onChange}
                      placeholder="Enter note content here..."
                      style={{ height: '350px', marginBottom: '50px' }}
                      theme="snow"
                    />
                  )}
                />
              </Box>
            </Box>
          </Stack>
        </Paper>

        <Button variant="outlined" onClick={handleCancel}>
          Cancel
        </Button>
      </Box>
    </Container>
  )
}

export default EditableNote
