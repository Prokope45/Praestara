import {
  Avatar,
  Box,
  Container,
  Typography,
  TextField,
  Stack,
  IconButton,
} from "@mui/material"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState, useRef } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FaCamera, FaTrash } from "react-icons/fa"

import {
  type ApiError,
  type UserPublic,
  type UserUpdateMe,
  UsersService,
} from "@/client"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { emailPattern, handleError } from "@/utils"
import { Button } from "../ui/button"

const UserInformation = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const { user: currentUser } = useAuth()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { isSubmitting, errors, isDirty },
  } = useForm<UserPublic>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      full_name: currentUser?.full_name,
      email: currentUser?.email,
    },
  })

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  const mutation = useMutation({
    mutationFn: (data: UserUpdateMe) =>
      UsersService.updateUserMe({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("User updated successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries()
    },
  })

  const uploadImageMutation = useMutation({
    mutationFn: (file: File) => {
      return UsersService.uploadProfileImage({ formData: { file } })
    },
    onSuccess: () => {
      showSuccessToast("Profile image updated successfully.")
      queryClient.invalidateQueries()
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const deleteImageMutation = useMutation({
    mutationFn: () => UsersService.deleteProfileImage(),
    onSuccess: () => {
      showSuccessToast("Profile image removed successfully.")
      queryClient.invalidateQueries()
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const handleImageClick = () => {
    fileInputRef.current?.click()
  }

  const handleImageChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      showErrorToast("Please select an image file")
      return
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      showErrorToast("Image size must be less than 5MB")
      return
    }

    uploadImageMutation.mutate(file)
  }

  const handleDeleteImage = () => {
    deleteImageMutation.mutate()
  }

  const onSubmit: SubmitHandler<UserUpdateMe> = async (data) => {
    mutation.mutate(data)
  }

  const onCancel = () => {
    reset()
    toggleEditMode()
  }

  const profileImage = currentUser?.profile_image || "/assets/images/default-avatar.svg"

  return (
    <Container maxWidth="lg">
      <Typography variant="h6" sx={{ py: 2 }}>
        User Information
      </Typography>
      <Box
        component="form"
        onSubmit={handleSubmit(onSubmit)}
        sx={{ maxWidth: { xs: '100%', md: '50%' } }}
      >
        <Stack spacing={3}>
          {/* Profile Image Section */}
          <Box>
            <Typography variant="body2" sx={{ mb: 2, fontWeight: 500 }}>
              Profile Image
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar
                src={profileImage}
                alt={currentUser?.full_name || "User"}
                sx={{ width: 100, height: 100 }}
              />
              <Stack direction="row" spacing={1}>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageChange}
                  accept="image/*"
                  style={{ display: 'none' }}
                />
                <IconButton
                  onClick={handleImageClick}
                  disabled={uploadImageMutation.isPending}
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': { bgcolor: 'primary.dark' },
                  }}
                >
                  <FaCamera />
                </IconButton>
                {currentUser?.profile_image && (
                  <IconButton
                    onClick={handleDeleteImage}
                    disabled={deleteImageMutation.isPending}
                    sx={{
                      bgcolor: 'error.main',
                      color: 'white',
                      '&:hover': { bgcolor: 'error.dark' },
                    }}
                  >
                    <FaTrash />
                  </IconButton>
                )}
              </Stack>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Click the camera icon to upload a new image (max 5MB)
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
              Full name
            </Typography>
            {editMode ? (
              <TextField
                {...register("full_name", { maxLength: 30 })}
                type="text"
                size="small"
                fullWidth
              />
            ) : (
              <Typography
                sx={{
                  py: 1,
                  color: !currentUser?.full_name ? 'text.secondary' : 'inherit',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '250px',
                }}
              >
                {currentUser?.full_name || "N/A"}
              </Typography>
            )}
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
              Email
            </Typography>
            {editMode ? (
              <TextField
                {...register("email", {
                  required: "Email is required",
                  pattern: emailPattern,
                })}
                type="email"
                size="small"
                fullWidth
                error={!!errors.email}
                helperText={errors.email?.message}
              />
            ) : (
              <Typography
                sx={{
                  py: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '250px',
                }}
              >
                {currentUser?.email}
              </Typography>
            )}
          </Box>
        </Stack>

        <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
          <Button
            variant="contained"
            onClick={editMode ? undefined : toggleEditMode}
            type={editMode ? "submit" : "button"}
            loading={editMode ? isSubmitting : false}
            disabled={editMode ? !isDirty || !getValues("email") : false}
          >
            {editMode ? "Save" : "Edit"}
          </Button>
          {editMode && (
            <Button
              variant="outlined"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          )}
        </Stack>
      </Box>
    </Container>
  )
}

export default UserInformation
