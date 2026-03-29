import {
  CircularProgress,
  Button as MuiButton,
  type ButtonProps as MuiButtonProps,
} from "@mui/material"
import * as React from "react"

interface ButtonLoadingProps {
  loading?: boolean
  loadingText?: React.ReactNode
}

export interface ButtonProps
  extends Omit<MuiButtonProps, "loading">,
    ButtonLoadingProps {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(props, ref) {
    const { loading, disabled, loadingText, children, ...rest } = props
    return (
      <MuiButton
        disabled={loading || disabled}
        ref={ref}
        {...rest}
        startIcon={
          loading && !loadingText ? (
            <CircularProgress size={16} color="inherit" />
          ) : (
            rest.startIcon
          )
        }
      >
        {loading && loadingText ? (
          <>
            <CircularProgress size={16} color="inherit" sx={{ mr: 1 }} />
            {loadingText}
          </>
        ) : (
          children
        )}
      </MuiButton>
    )
  },
)
