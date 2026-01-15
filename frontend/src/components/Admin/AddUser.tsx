import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { Box, Stack, TextField, Typography, FormControlLabel } from '@mui/material'
import { useState } from "react"
import { FaPlus } from "react-icons/fa"

import { type UserCreate, UsersService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { emailPattern, handleError } from "@/utils"
import { Checkbox } from "../ui/checkbox"
import {
  DialogRoot,
  DialogTitle,
  DialogContent,
  DialogFooter,
} from "../ui/dialog"
import { Button } from "../ui/button"

interface UserCreateForm extends UserCreate {
  confirm_password: string
}

const AddUser = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const {
    control,
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isValid, isSubmitting },
  } = useForm<UserCreateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
      is_superuser: false,
      is_active: false,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: UserCreate) =>
      UsersService.createUser({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("User created successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const onSubmit: SubmitHandler<UserCreateForm> = (data) => {
    mutation.mutate(data)
  }

  return (
    <>
      <Button
        variant="contained"
        startIcon={<FaPlus />}
        onClick={() => setIsOpen(true)}
        sx={{ my: 4 }}
      >
        Add User
      </Button>

      <DialogRoot
        open={isOpen}
        onOpenChange={(open) => setIsOpen(open)}
        maxWidth="md"
        fullWidth
      >
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>Add User</DialogTitle>
          <DialogContent>
            <Typography sx={{ mb: 2 }}>
              Fill in the form below to add a new user to the system.
            </Typography>
            <Stack spacing={3} sx={{ mt: 2 }}>
              <TextField
                id="email"
                label="Email"
                required
                fullWidth
                type="email"
                error={!!errors.email}
                helperText={errors.email?.message}
                {...register("email", {
                  required: "Email is required",
                  pattern: emailPattern,
                })}
                placeholder="Email"
              />

              <TextField
                id="name"
                label="Full Name"
                fullWidth
                error={!!errors.full_name}
                helperText={errors.full_name?.message}
                {...register("full_name")}
                placeholder="Full name"
              />

              <TextField
                id="password"
                label="Set Password"
                required
                fullWidth
                type="password"
                error={!!errors.password}
                helperText={errors.password?.message}
                {...register("password", {
                  required: "Password is required",
                  minLength: {
                    value: 8,
                    message: "Password must be at least 8 characters",
                  },
                })}
                placeholder="Password"
              />

              <TextField
                id="confirm_password"
                label="Confirm Password"
                required
                fullWidth
                type="password"
                error={!!errors.confirm_password}
                helperText={errors.confirm_password?.message}
                {...register("confirm_password", {
                  required: "Please confirm your password",
                  validate: (value) =>
                    value === getValues().password ||
                    "The passwords do not match",
                })}
                placeholder="Password"
              />

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Controller
                  control={control}
                  name="is_superuser"
                  render={({ field }) => (
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={field.value}
                          onChange={(e) => field.onChange(e.target.checked)}
                        />
                      }
                      label="Is superuser?"
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="is_active"
                  render={({ field }) => (
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={field.value}
                          onChange={(e) => field.onChange(e.target.checked)}
                        />
                      }
                      label="Is active?"
                    />
                  )}
                />
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

export default AddUser
