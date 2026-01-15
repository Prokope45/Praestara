import * as React from "react"
import { FormControl, FormLabel, FormHelperText, FormControlProps } from "@mui/material"

export interface FieldProps extends FormControlProps {
  label?: React.ReactNode
  helperText?: React.ReactNode
  errorText?: React.ReactNode
  optionalText?: React.ReactNode
  invalid?: boolean
}

export const Field = React.forwardRef<HTMLDivElement, FieldProps>(
  function Field(props, ref) {
    const { label, children, helperText, errorText, optionalText, invalid, ...rest } =
      props
    return (
      <FormControl ref={ref} error={invalid} {...rest}>
        {label && (
          <FormLabel>
            {label}
            {optionalText && <span style={{ marginLeft: 4 }}>{optionalText}</span>}
          </FormLabel>
        )}
        {children}
        {helperText && !invalid && (
          <FormHelperText>{helperText}</FormHelperText>
        )}
        {errorText && invalid && (
          <FormHelperText error>{errorText}</FormHelperText>
        )}
      </FormControl>
    )
  },
)
