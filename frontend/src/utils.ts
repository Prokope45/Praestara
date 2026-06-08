import { enqueueSnackbar } from 'notistack'
import type { ApiError } from "./client"
import useCustomToast from "./hooks/useCustomToast"

export const emailPattern = {
  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
  message: "Invalid email address",
}

export const namePattern = {
  value: /^[A-Za-z\sÀ-ſ]{1,30}$/,
  message: "Invalid name",
}

export const passwordRules = (isRequired = true) => {
  const rules: any = {
    minLength: {
      value: 8,
      message: "Password must be at least 8 characters",
    },
  }

  if (isRequired) {
    rules.required = "Password is required"
  }

  return rules
}

export const confirmPasswordRules = (
  getValues: () => any,
  isRequired = true,
) => {
  const rules: any = {
    validate: (value: string) => {
      const password = getValues().password || getValues().new_password
      return value === password ? true : "The passwords do not match"
    },
  }

  if (isRequired) {
    rules.required = "Password confirmation is required"
  }

  return rules
}

// Plain function — uses notistack's standalone API (works outside React components)
export const handleError = (err: ApiError) => {
  const errDetail = (err.body as any)?.detail
  let errorMessage = errDetail || "Something went wrong."
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    errorMessage = errDetail[0].msg
  }
  enqueueSnackbar(errorMessage, {
    variant: 'error',
    anchorOrigin: { vertical: 'top', horizontal: 'right' },
  })
}

// Hook version — kept for useAuth.ts compatibility
export const useHandleError = () => {
  const { showErrorToast } = useCustomToast()
  return (err: ApiError) => {
    const errDetail = (err.body as any)?.detail
    let errorMessage = errDetail || "Something went wrong."
    if (Array.isArray(errDetail) && errDetail.length > 0) {
      errorMessage = errDetail[0].msg
    }
    showErrorToast(errorMessage)
  }
}
