import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm, Controller } from "react-hook-form"
import { Box, Stack, TextField, Typography } from '@mui/material'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { useState } from "react"
import { FaPlus } from "react-icons/fa"

import { type ItemCreate, ItemsService } from "../../client"
import type { ApiError } from "../../client/core/ApiError"
import useCustomToast from "../../hooks/useCustomToast"
import { handleError } from "../../utils"
import {
  DialogRoot,
  DialogTitle,
  DialogContent,
  DialogFooter,
} from "../ui/dialog"
import { Button } from "../ui/button"

const AddNote = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isValid, isSubmitting },
  } = useForm<ItemCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      title: "",
      description: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: ItemCreate) =>
      ItemsService.createItem({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Note created successfully.")
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

  const onSubmit: SubmitHandler<ItemCreate> = (data) => {
    mutation.mutate(data)
  }

  return (
    <>
      <Button
        variant="contained"
        startIcon={<FaPlus />}
        onClick={() => setIsOpen(true)}
      >
        Add Note
      </Button>

      <DialogRoot
        open={isOpen}
        onOpenChange={(open) => setIsOpen(open)}
        maxWidth="md"
        fullWidth
      >
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>Add Note</DialogTitle>
          <DialogContent>
            <Typography sx={{ mb: 2 }}>
              Fill in the details to add a new note.
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
                  required: "Title is required.",
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
                        style={{ height: '250px', marginBottom: '50px', width: '100%' }}
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
              disabled={!isValid}
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

export default AddNote
